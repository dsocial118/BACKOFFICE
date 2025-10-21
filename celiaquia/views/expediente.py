import json
import logging
import time
import traceback
import io


from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    FileResponse,
)
from django.utils.html import escape
from django.views.decorators.csrf import csrf_protect
from django.contrib import messages
from django.core.exceptions import ValidationError, PermissionDenied, ObjectDoesNotExist
from django.conf import settings
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.core.paginator import Paginator

from celiaquia.forms import ExpedienteForm, ConfirmarEnvioForm
from celiaquia.models import (
    AsignacionTecnico,
    EstadoLegajo,
    Expediente,
    ExpedienteCiudadano,
    RevisionTecnico,
)
from celiaquia.services.ciudadano_service import CiudadanoService
from celiaquia.services.expediente_service import (
    ExpedienteService,
    _set_estado,
)
from celiaquia.services.importacion_service import ImportacionService
from celiaquia.services.cruce_service import CruceService
from celiaquia.services.cupo_service import CupoService, CupoNoConfigurado
from django.utils import timezone
from core.models import Provincia, Localidad

logger = logging.getLogger("django")


def _user_in_group(user, group_name: str) -> bool:
    return user.is_authenticated and user.groups.filter(name=group_name).exists()


def _is_admin(user) -> bool:
    return user.is_authenticated and user.is_superuser


def _is_ajax(request) -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def _is_provincial(user) -> bool:
    if not user.is_authenticated:
        return False
    try:
        return bool(user.profile.es_usuario_provincial and user.profile.provincia_id)
    except ObjectDoesNotExist:
        return False


def _user_provincia(user):
    try:
        return user.profile.provincia
    except ObjectDoesNotExist:
        return None


def _parse_limit(value, default=None, max_cap=5000):
    if value is None:
        return default
    txt = str(value).strip().lower()
    if txt in ("all", "todos", "0", "none"):
        return None
    try:
        n = int(txt)
        if n <= 0:
            return None
        return min(n, max_cap) if max_cap is not None else n
    except Exception:
        return default


class LocalidadesLookupView(View):
    """Provide a JSON list of localidades filtered by provincia and municipio."""

    def get(self, request):
        user = request.user
        provincia_id = request.GET.get("provincia")
        municipio_id = request.GET.get("municipio")

        localidades = Localidad.objects.select_related("municipio__provincia")

        # Filtrar por provincia del usuario si es provincial
        if _is_provincial(user):
            prov = _user_provincia(user)
            if prov:
                localidades = localidades.filter(municipio__provincia=prov)

        if provincia_id:
            localidades = localidades.filter(municipio__provincia_id=provincia_id)
        if municipio_id:
            localidades = localidades.filter(municipio_id=municipio_id)

        data = [
            {
                "provincia_id": loc.municipio.provincia_id if loc.municipio else None,
                "provincia_nombre": (
                    loc.municipio.provincia.nombre
                    if loc.municipio and loc.municipio.provincia
                    else None
                ),
                "municipio_id": loc.municipio_id,
                "municipio_nombre": loc.municipio.nombre if loc.municipio else None,
                "localidad_id": loc.id,
                "localidad_nombre": loc.nombre,
            }
            for loc in localidades.order_by(
                "municipio__provincia__nombre", "municipio__nombre", "nombre"
            )
        ]
        return JsonResponse(data, safe=False)


class ExpedienteListView(ListView):
    model = Expediente
    template_name = "celiaquia/expediente_list.html"
    context_object_name = "expedientes"
    paginate_by = 20

    def get_paginate_by(self, queryset):
        page_size = self.request.GET.get("page_size", "20")
        if page_size.lower() in ("all", "todos"):
            return None
        try:
            return int(page_size)
        except (ValueError, TypeError):
            return 20

    def get_queryset(self):
        user = self.request.user
        qs = (
            Expediente.objects.select_related(
                "estado",
                "usuario_provincia__profile__provincia",
            )
            .prefetch_related("asignaciones_tecnicos__tecnico")
            .annotate(
                legajos_subsanar_count=Count(
                    "expediente_ciudadanos",
                    filter=Q(expediente_ciudadanos__revision_tecnico="SUBSANAR"),
                )
            )
            .only(
                "id",
                "fecha_creacion",
                "estado__nombre",
                "usuario_provincia_id",
                "usuario_provincia__profile__id",
                "usuario_provincia__profile__provincia_id",
                "usuario_provincia__profile__provincia__id",
                "usuario_provincia__profile__provincia__nombre",
            )
        )
        if _is_admin(user):
            return qs.order_by("-fecha_creacion")
        if _user_in_group(user, "CoordinadorCeliaquia"):
            return qs.filter(
                estado__nombre__in=["CONFIRMACION_DE_ENVIO", "RECEPCIONADO", "ASIGNADO"]
            ).order_by("-fecha_creacion")
        if _user_in_group(user, "TecnicoCeliaquia"):
            return (
                qs.filter(asignaciones_tecnicos__tecnico=user)
                .distinct()
                .order_by("-fecha_creacion")
            )
        if _is_provincial(user):
            prov = _user_provincia(user)
            return qs.filter(usuario_provincia__profile__provincia=prov).order_by(
                "-fecha_creacion"
            )
        return qs.filter(usuario_provincia=user).order_by("-fecha_creacion")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["tecnicos"] = []
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            ctx["tecnicos"] = User.objects.filter(
                groups__name="TecnicoCeliaquia"
            ).order_by("last_name", "first_name")
        return ctx


@method_decorator(csrf_protect, name="dispatch")
class ProcesarExpedienteView(View):
    def post(self, request, pk):
        user = self.request.user
        logger.info("=" * 80)
        logger.info("INICIANDO PROCESAMIENTO DE EXPEDIENTE %s", pk)
        logger.info("Usuario: %s (ID: %s)", user.username, user.id)
        
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            logger.info("Usuario provincial - Provincia: %s", prov)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)
        
        logger.info("Expediente encontrado: ID=%s, Estado=%s", expediente.id, expediente.estado.nombre)
        logger.info("Archivo Excel: %s", expediente.excel_masivo.name if expediente.excel_masivo else "NO HAY ARCHIVO")

        try:
            logger.info("Llamando a ExpedienteService.procesar_expediente...")
            result = ExpedienteService.procesar_expediente(expediente, user)
            logger.info("Resultado del procesamiento: %s", result)

            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "creados": result.get("creados", 0),
                        "errores": result.get("errores", 0),
                        "excluidos": result.get("excluidos", 0),
                        "excluidos_detalle": result.get("excluidos_detalle", []),
                    }
                )

            creados = result.get('creados', 0)
            errores_count = result.get('errores', 0)
            detalles = result.get('detalles_errores', [])
            
            logger.info("Creados: %s, Errores: %s", creados, errores_count)
            if detalles:
                logger.error("DETALLES DE ERRORES:")
                for det in detalles:
                    logger.error("  - Fila %s: %s", det.get('fila'), det.get('error'))
            
            mensaje_principal = f"¡Listo! Se crearon {creados} legajos y el expediente pasó a EN ESPERA."
            
            if errores_count > 0:
                mensaje_principal += f" Hubo {errores_count} errores."
                if detalles:
                    errores_html = "<br><strong>Detalles de errores:</strong><br>"
                    errores_html += "<br>".join([f"• Fila {d.get('fila')}: {escape(d.get('error'))}" for d in detalles[:15]])
                    if len(detalles) > 15:
                        errores_html += f"<br>... y {len(detalles) - 15} errores más (revisa los logs)"
                    messages.error(request, errores_html)
            
            messages.success(request, mensaje_principal)
            logger.info("Mensajes agregados correctamente")

            excluidos_count = result.get("excluidos", 0)
            if excluidos_count:
                det = result.get("excluidos_detalle", [])
                preview = []
                for d in det[:10]:
                    doc = d.get("documento", "")
                    ape = d.get("apellido", "")
                    nom = d.get("nombre", "")
                    estado = d.get("estado_programa") or d.get("motivo") or "-"
                    expid = d.get("expediente_origen_id", "-")
                    preview.append(f"• {doc} — {ape}, {nom} ({estado}) — Exp #{expid}")

                extra = ""
                if len(det) > 10:
                    extra = f"<br>… y {len(det) - 10} más."

                # Escapar contenido para prevenir XSS
                preview_escaped = [escape(p) for p in preview]
                extra_escaped = escape(extra) if extra else ""
                html = (
                    f"Se excluyeron {excluidos_count} registros porque ya están en otro expediente:"
                    f"<br>{'<br>'.join(preview_escaped)}{extra_escaped}"
                )
                messages.warning(request, html)

            return redirect("expediente_detail", pk=pk)

        except ValidationError as ve:
            logger.error("ValidationError en expediente %s: %s", pk, str(ve))
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(ve))}, status=400
                )
            messages.error(request, f"Error de validación: {escape(str(ve))}")
            logger.info("Redirigiendo a expediente_detail después de ValidationError")
            return redirect("expediente_detail", pk=pk)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error("="*80)
            logger.error("EXCEPCIÓN CAPTURADA en expediente %s", pk)
            logger.error("Tipo de error: %s", type(e).__name__)
            logger.error("Mensaje: %s", str(e))
            logger.error("Traceback completo:\n%s", tb)
            logger.error("="*80)
            error_msg = f"Error al procesar: {escape(str(e))}"
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": error_msg}, status=500
                )
            messages.error(request, error_msg)
            logger.info("Redirigiendo a expediente_detail después de Exception")
            return redirect("expediente_detail", pk=pk)


class CrearLegajosView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            payload = json.loads(request.body)
            rows = payload.get("rows", [])
        except json.JSONDecodeError:
            return HttpResponseBadRequest("JSON inválido.")

        estado_inicial, _ = EstadoLegajo.objects.get_or_create(
            nombre="DOCUMENTO_PENDIENTE"
        )
        creados = existentes = 0
        for datos in rows:
            ciudadano = CiudadanoService.get_or_create_ciudadano(datos, user)
            _, was_created = ExpedienteCiudadano.objects.get_or_create(
                expediente=expediente,
                ciudadano=ciudadano,
                defaults={"estado": estado_inicial},
            )
            if was_created:
                creados += 1
            else:
                existentes += 1
        return JsonResponse({"creados": creados, "existentes": existentes})


class ExpedientePlantillaExcelView(View):
    """Genera un archivo de Excel vacío con los campos requeridos para un expediente."""

    def get(self, request, *args, **kwargs):
        content = ImportacionService.generar_plantilla_excel()
        response = HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="plantilla_expediente.xlsx"'
        )
        return response


@method_decorator(csrf_protect, name="dispatch")
class ExpedientePreviewExcelView(View):
    def post(self, request, *args, **kwargs):
        logger.debug("PREVIEW: %s %s", request.method, request.path)
        archivo = request.FILES.get("excel_masivo")
        if not archivo:
            return JsonResponse({"error": "No se recibió ningún archivo."}, status=400)

        raw_limit = request.POST.get("limit") or request.GET.get("limit")
        max_rows = _parse_limit(raw_limit, default=None, max_cap=5000)

        try:
            preview = ImportacionService.preview_excel(archivo, max_rows=max_rows)
            return JsonResponse(preview)
        except ValidationError as e:
            return JsonResponse({"error": str(e)}, status=400)
        except Exception:
            tb = traceback.format_exc()
            logger.error("PREVIEW error:\n%s", tb)
            return JsonResponse({"error": "Error inesperado al procesar."}, status=500)


class ExpedienteCreateView(CreateView):
    """Formulario para la creación de expedientes provinciales."""

    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        # Filtrar provincias según el usuario
        if _is_provincial(user):
            # Usuario provincial: solo su provincia
            prov = _user_provincia(user)
            ctx["provincias"] = [prov] if prov else []
        else:
            # Admin/Coordinador: todas las provincias
            ctx["provincias"] = Provincia.objects.order_by("nombre")
        return ctx

    def form_valid(self, form):
        # Verificar si hay datos editados desde el frontend
        datos_editados_json = self.request.POST.get('datos_editados')
        excel_file = form.cleaned_data["excel_masivo"]
        
        if datos_editados_json:
            try:
                import json
                from io import BytesIO
                import pandas as pd
                
                datos_editados = json.loads(datos_editados_json)
                
                # Crear nuevo Excel con datos editados
                df = pd.DataFrame(datos_editados)
                # Remover columna ID si existe
                if 'ID' in df.columns:
                    df = df.drop('ID', axis=1)
                
                output = BytesIO()
                df.to_excel(output, index=False, engine='openpyxl')
                output.seek(0)
                
                # Crear archivo temporal con datos editados
                from django.core.files.uploadedfile import InMemoryUploadedFile
                excel_file = InMemoryUploadedFile(
                    output,
                    'excel_masivo',
                    'expediente_editado.xlsx',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    output.getbuffer().nbytes,
                    None
                )
            except Exception as e:
                logger.error(f"Error procesando datos editados: {e}")
                messages.error(self.request, "Error al procesar los datos editados.")
                return redirect("expediente_list")
        
        expediente = ExpedienteService.create_expediente(
            usuario_provincia=self.request.user,
            datos_metadatos=form.cleaned_data,
            excel_masivo=excel_file,
        )
        messages.success(self.request, "Expediente creado correctamente.")
        return redirect("expediente_detail", pk=expediente.pk)


class ExpedienteDetailView(DetailView):
    """Detalle del expediente con información relacionada."""

    model = Expediente
    template_name = "celiaquia/expediente_detail.html"
    context_object_name = "expediente"

    def get_queryset(self):
        user = self.request.user
        base = Expediente.objects.select_related(
            "estado", "usuario_modificador", "usuario_provincia"
        ).prefetch_related(
            "expediente_ciudadanos__ciudadano",
            "expediente_ciudadanos__estado",
            "asignaciones_tecnicos__tecnico",
        )
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            return base
        if _user_in_group(user, "TecnicoCeliaquia"):
            return base.filter(asignaciones_tecnicos__tecnico=user)
        if _is_provincial(user):
            prov = _user_provincia(user)
            return base.filter(usuario_provincia__profile__provincia=prov)
        return base.filter(usuario_provincia=user)

    def get_context_data(self, **kwargs):
        """Arma el contexto con métricas y paginación del historial."""

        ctx = super().get_context_data(**kwargs)
        expediente = self.object
        user = self.request.user

        preview = preview_error = None
        preview_limit_actual = None

        q = expediente.expediente_ciudadanos.select_related("ciudadano", "estado")
        counts = q.aggregate(
            c_aceptados=Count(
                "id",
                filter=Q(revision_tecnico="APROBADO", resultado_sintys="MATCH"),
            ),
            c_rech_tecnico=Count("id", filter=Q(revision_tecnico="RECHAZADO")),
            c_rech_sintys=Count(
                "id",
                filter=Q(revision_tecnico="APROBADO", resultado_sintys="NO_MATCH"),
            ),
            c_subsanar=Count("id", filter=Q(revision_tecnico=RevisionTecnico.SUBSANAR)),
        )
        ctx["hay_subsanar"] = counts["c_subsanar"] > 0
        ctx["legajos_aceptados"] = q.filter(
            revision_tecnico="APROBADO", resultado_sintys="MATCH"
        )
        ctx["legajos_rech_tecnico"] = q.filter(revision_tecnico="RECHAZADO")
        ctx["legajos_rech_sintys"] = q.filter(
            revision_tecnico="APROBADO", resultado_sintys="NO_MATCH"
        )
        ctx["legajos_subsanar"] = q.filter(revision_tecnico=RevisionTecnico.SUBSANAR)

        # Enriquecer legajos con informacion de tipo (hijo/responsable)
        from celiaquia.services.legajo_service import LegajoService
        from celiaquia.services.familia_service import FamiliaService

        legajos_enriquecidos = []
        legajos_list = list(q.all())
        legajos_por_ciudadano = {}
        ciudadanos_ids = [leg.ciudadano_id for leg in legajos_list]
        responsables_ids = set()
        if ciudadanos_ids:
            try:
                responsables_ids = FamiliaService.obtener_ids_responsables(
                    ciudadanos_ids
                )
            except Exception as exc:
                logger.warning(
                    "No se pudo resolver responsables para expediente %s: %s",
                    expediente.id,
                    exc,
                )

        # Enriquecer legajos con información de responsable/hijo
        responsables_legajos = []
        hijos_por_responsable = {}
        hijos_sin_responsable = []

        for legajo in legajos_list:
            legajo.es_responsable = LegajoService._es_responsable(
                legajo.ciudadano, responsables_ids
            )
            legajo.tipo_legajo = "Responsable" if legajo.es_responsable else "Hijo"
            legajo.archivos_requeridos = (
                LegajoService.get_archivos_requeridos_por_legajo(
                    legajo, responsables_ids
                )
            )

            if legajo.es_responsable:
                legajo.hijos_a_cargo = FamiliaService.obtener_hijos_a_cargo(
                    legajo.ciudadano.id, expediente
                )
                legajo.responsable_id = None
                responsables_legajos.append(legajo)
            else:
                legajo.hijos_a_cargo = []
                legajo.responsable_id = FamiliaService.obtener_responsable_de_hijo(
                    legajo.ciudadano.id
                )
                if legajo.responsable_id:
                    if legajo.responsable_id not in hijos_por_responsable:
                        hijos_por_responsable[legajo.responsable_id] = []
                    hijos_por_responsable[legajo.responsable_id].append(legajo)
                else:
                    hijos_sin_responsable.append(legajo)

            legajos_por_ciudadano[legajo.ciudadano_id] = legajo

        # Ordenar: responsables primero, luego sus hijos, luego hijos sin responsable
        for responsable in responsables_legajos:
            legajos_enriquecidos.append(responsable)
            # Agregar hijos de este responsable inmediatamente después
            hijos = hijos_por_responsable.get(responsable.ciudadano_id, [])
            legajos_enriquecidos.extend(hijos)

        # Agregar hijos sin responsable al final
        legajos_enriquecidos.extend(hijos_sin_responsable)

        faltantes_list = LegajoService.faltantes_archivos(expediente)
        # Obtener estructura familiar completa
        estructura_familiar = FamiliaService.obtener_estructura_familiar_expediente(
            expediente
        )

        # Enriquecer estructura familiar con referencia a legajos
        for info in estructura_familiar.get("responsables", {}).values():
            for hijo in info.get("hijos", []):
                hijo.legajo_relacionado = legajos_por_ciudadano.get(hijo.id)

        ctx["legajos_enriquecidos"] = legajos_enriquecidos
        ctx["estructura_familiar"] = estructura_familiar

        ctx["c_aceptados"] = counts["c_aceptados"]
        ctx["c_rech_tecnico"] = counts["c_rech_tecnico"]
        ctx["c_rech_sintys"] = counts["c_rech_sintys"]
        ctx["c_subsanar"] = counts["c_subsanar"]

        if expediente.estado.nombre == "CREADO" and expediente.excel_masivo:
            raw_limit = self.request.GET.get("preview_limit")
            max_rows = _parse_limit(raw_limit, default=None, max_cap=5000)
            preview_limit_actual = (
                raw_limit if raw_limit is not None else str(max_rows or "all")
            )
            try:
                preview = ImportacionService.preview_excel(
                    expediente.excel_masivo, max_rows=max_rows
                )
            except Exception as e:
                preview_error = str(e)

        preview_limit_opciones = ["5", "10", "20", "50", "100", "all"]

        tecnicos = []
        if _is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia"):
            tecnicos = User.objects.filter(groups__name="TecnicoCeliaquia").order_by(
                "last_name", "first_name"
            )

        faltan_archivos = expediente.expediente_ciudadanos.filter(
            Q(archivo2__isnull=True) | Q(archivo3__isnull=True)
        ).exists()

        # Cupo: usar propiedad expediente.provincia (puede ser None)
        cupo = None
        cupo_metrics = None
        cupo_error = None
        prov = getattr(expediente, "provincia", None)
        if prov:
            try:
                cupo_metrics = CupoService.metrics_por_provincia(prov)
                cupo = cupo_metrics
            except CupoNoConfigurado:
                cupo_error = "La provincia no tiene cupo configurado."
        else:
            cupo_error = "No se pudo determinar la provincia del expediente."

        fuera_count = expediente.expediente_ciudadanos.filter(
            estado_cupo="FUERA"
        ).count()
        ctx["fuera_de_cupo"] = q.filter(estado_cupo="FUERA")

        historial = expediente.historial.select_related(
            "estado_anterior", "estado_nuevo", "usuario"
        )
        ctx["historial_page_obj"] = Paginator(historial, 5).get_page(
            self.request.GET.get("historial_page")
        )

        ctx.update(
            {
                "legajos": legajos_enriquecidos,
                "confirm_form": ConfirmarEnvioForm(),
                "preview": preview,
                "preview_error": preview_error,
                "preview_limit_actual": str(preview_limit_actual or "5").lower(),
                "preview_limit_opciones": preview_limit_opciones,
                "tecnicos": tecnicos,
                "faltan_archivos": faltan_archivos,
                "faltantes_archivos_detalle": faltantes_list,
                "cupo": cupo,  # para el template actual
                "cupo_metrics": cupo_metrics,  # compat si lo usas en JS/otros templates
                "cupo_error": cupo_error,
                "fuera_count": fuera_count,
                "total_responsables": len(estructura_familiar.get("responsables", {})),
                "total_hijos_sin_responsable": len(
                    estructura_familiar.get("hijos_sin_responsable", [])
                ),
            }
        )
        return ctx


class ExpedienteImportView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        try:
            result = ImportacionService.importar_legajos_desde_excel(
                expediente, expediente.excel_masivo, user
            )
            detalles = result.get("detalles_errores") or []
            resumen = ""
            if detalles:
                resumen = "; ".join(
                    f"Fila {d.get('fila')}: {d.get('error')}" for d in detalles[:5]
                )
                if len(detalles) > 5:
                    resumen += " (ver logs para más detalles)"

            mensaje_principal = f"Importación: {result['validos']} válidos, {result['errores']} errores."
            if resumen:
                mensaje_principal += f" Detalles: {resumen}"
            messages.success(request, mensaje_principal)

            if detalles:
                messages.error(request, f"Errores detectados: {resumen}")

            advertencias = result.get("warnings") or []
            if advertencias:
                resumen_warn = "; ".join(
                    f"Fila {w.get('fila')}: {w.get('detalle')}"
                    for w in advertencias[:5]
                )
                if len(advertencias) > 5:
                    resumen_warn += " (se muestran las primeras 5)"
                messages.warning(request, f"Advertencias: {resumen_warn}")
        except ValidationError as ve:
            messages.error(request, f"Error de validación: {ve.message}")
        except Exception as e:
            messages.error(request, f"Error inesperado: {e}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteConfirmView(View):
    def post(self, request, pk):
        user = self.request.user
        if _is_admin(user):
            expediente = get_object_or_404(Expediente, pk=pk)
        elif _is_provincial(user):
            prov = _user_provincia(user)
            expediente = get_object_or_404(
                Expediente, pk=pk, usuario_provincia__profile__provincia=prov
            )
        else:
            expediente = get_object_or_404(Expediente, pk=pk, usuario_provincia=user)

        faltantes_qs = expediente.expediente_ciudadanos.filter(
            Q(archivo2__isnull=True) | Q(archivo3__isnull=True)
        )
        if faltantes_qs.exists():
            msg = "No se puede enviar: hay legajos sin los 2 archivos requeridos."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        try:
            result = ExpedienteService.confirmar_envio(expediente, user)
            if _is_ajax(request):
                return JsonResponse(
                    {
                        "success": True,
                        "message": "Expediente enviado a Subsecretaría.",
                        "validos": result["validos"],
                        "errores": result["errores"],
                    }
                )
            messages.success(
                request,
                f"Expediente enviado a Subsecretaría. Legajos: {result['validos']} (sin errores).",
            )
        except ValidationError as ve:
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(ve))}, status=400
                )
            messages.error(request, f"Error al confirmar: {escape(str(ve))}")
        except Exception as e:
            logger.error("Error inesperado al confirmar envío: %s", e, exc_info=True)
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": escape(str(e))}, status=500
                )
            messages.error(request, f"Error inesperado: {escape(str(e))}")
        return redirect("expediente_detail", pk=pk)


class ExpedienteUpdateView(UpdateView):
    model = Expediente
    form_class = ExpedienteForm
    template_name = "celiaquia/expediente_form.html"

    def get_success_url(self):
        return reverse_lazy("expediente_detail", args=[self.object.pk])


class RecepcionarExpedienteView(View):
    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )
            raise PermissionDenied(
                "No tiene permisos para recepcionar este expediente."
            )

        expediente = get_object_or_404(Expediente, pk=pk)
        if expediente.estado.nombre != "CONFIRMACION_DE_ENVIO":
            msg = "El expediente no está pendiente de recepción."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.warning(request, msg)
            return redirect("expediente_detail", pk=pk)

        _set_estado(expediente, "RECEPCIONADO", user)

        if _is_ajax(request):
            return JsonResponse(
                {"success": True, "message": "Recepcionado correctamente."}
            )
        messages.success(
            request,
            "Expediente recepcionado correctamente. Ahora puede asignar un técnico.",
        )
        return redirect("expediente_detail", pk=pk)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


class AsignarTecnicoView(View):
    def post(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            if _is_ajax(request):
                return JsonResponse(
                    {"success": False, "error": "Permiso denegado."}, status=403
                )
            raise PermissionDenied("No tiene permisos para asignar técnico.")

        expediente = get_object_or_404(Expediente, pk=pk)

        tecnico_id = request.POST.get("tecnico_id")
        if not tecnico_id:
            msg = "No se seleccionó ningún técnico."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        tecnico_qs = User.objects.filter(groups__name="TecnicoCeliaquia")
        tecnico = get_object_or_404(tecnico_qs, pk=tecnico_id)

        estado_actual = expediente.estado.nombre
        if estado_actual not in ("RECEPCIONADO", "ASIGNADO"):
            msg = "Primero debe recepcionar el expediente."
            if _is_ajax(request):
                return JsonResponse({"success": False, "error": msg}, status=400)
            messages.error(request, msg)
            return redirect("expediente_detail", pk=pk)

        AsignacionTecnico.objects.get_or_create(
            expediente=expediente,
            tecnico=tecnico,
        )

        _set_estado(expediente, "ASIGNADO", user)

        if _is_ajax(request):
            return JsonResponse(
                {
                    "success": True,
                    "message": "Técnico asignado correctamente. Estado: ASIGNADO.",
                }
            )
        messages.success(
            request,
            f"Técnico {tecnico.get_full_name() or tecnico.username} asignado correctamente. Estado: ASIGNADO.",
        )
        return redirect("expediente_detail", pk=pk)

    def delete(self, request, pk):
        user = self.request.user
        if not (_is_admin(user) or _user_in_group(user, "CoordinadorCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        expediente = get_object_or_404(Expediente, pk=pk)
        tecnico_id = request.GET.get("tecnico_id")

        if not tecnico_id:
            return JsonResponse(
                {"success": False, "error": "ID de técnico requerido."}, status=400
            )

        try:
            asignacion = AsignacionTecnico.objects.get(
                expediente=expediente, tecnico_id=tecnico_id
            )
            asignacion.delete()
            return JsonResponse(
                {"success": True, "message": "Técnico removido correctamente."}
            )
        except AsignacionTecnico.DoesNotExist:
            return JsonResponse(
                {"success": False, "error": "Asignación no encontrada."}, status=404
            )


class ExpedienteNominaSintysExportView(View):
    """Descarga la nómina del expediente en formato compatible con Sintys."""

    def get(self, request, pk):
        expediente = get_object_or_404(Expediente, pk=pk)
        content = CruceService.generar_nomina_sintys_excel(expediente)
        filename = f"nomina_sintys_{expediente.pk}.xlsx"
        return FileResponse(io.BytesIO(content), as_attachment=True, filename=filename)


class SubirCruceExcelView(View):
    def post(self, request, pk):
        user = self.request.user

        if not (_is_admin(user) or _user_in_group(user, "TecnicoCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        expediente = get_object_or_404(Expediente, pk=pk)

        if not _is_admin(user):
            # Usar prefetch para evitar query adicional
            tecnicos_ids = [
                t.tecnico_id for t in expediente.asignaciones_tecnicos.all()
            ]
            if user.id not in tecnicos_ids:
                return JsonResponse(
                    {
                        "success": False,
                        "error": "No sos un técnico asignado a este expediente.",
                    },
                    status=403,
                )

        archivo = request.FILES.get("archivo")
        if not archivo:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Debe adjuntar un Excel con columna 'documento'.",
                },
                status=400,
            )

        try:
            resumen = CruceService.procesar_cruce_por_cuit(expediente, archivo, user)
            return JsonResponse(
                {
                    "success": True,
                    "message": "Cruce finalizado. Se generó el PRD del expediente.",
                    "resumen": resumen,
                }
            )
        except ValidationError as ve:
            return JsonResponse(
                {"success": False, "error": escape(str(ve))}, status=400
            )
        except Exception as e:
            logger.error("Error en cruce por CUIT: %s", e, exc_info=True)
            return JsonResponse({"success": False, "error": escape(str(e))}, status=500)

    def get(self, *_a, **_k):
        return HttpResponseNotAllowed(["POST"])


@method_decorator(csrf_protect, name="dispatch")
class RevisarLegajoView(View):
    def post(self, request, pk, legajo_id):
        user = request.user
        expediente = get_object_or_404(Expediente, pk=pk)

        # Permisos: admin o técnico
        if not (_is_admin(user) or _user_in_group(user, "TecnicoCeliaquia")):
            return JsonResponse(
                {"success": False, "error": "Permiso denegado."}, status=403
            )

        # Si no es admin, debe ser el técnico asignado a este expediente
        if not _is_admin(user):
            # Usar prefetch para evitar query adicional
            tecnicos_ids = [
                t.tecnico_id for t in expediente.asignaciones_tecnicos.all()
            ]
            if user.id not in tecnicos_ids:
                return JsonResponse(
                    {"success": False, "error": "No sos un técnico asignado."},
                    status=403,
                )

        leg = get_object_or_404(
            ExpedienteCiudadano, pk=legajo_id, expediente=expediente
        )

        accion = (request.POST.get("accion") or "").upper()
        if accion not in ("APROBAR", "RECHAZAR", "SUBSANAR"):
            return JsonResponse(
                {"success": False, "error": "Acción inválida."}, status=400
            )

        # Si RECHAZAR / SUBSANAR y estaba dentro de cupo -> liberar
        if accion in ("RECHAZAR", "SUBSANAR") and leg.estado_cupo == "DENTRO":
            try:
                CupoService.liberar_slot(
                    legajo=leg,
                    usuario=user,
                    motivo=f"Salida del cupo por {accion.lower()} técnico en expediente",
                )
                leg.estado_cupo = "NO_EVAL"
                leg.es_titular_activo = False
            except Exception as e:
                logger.error(
                    "Error al liberar cupo para legajo %s: %s", leg.pk, e, exc_info=True
                )

        if accion == "APROBAR":
            leg.revision_tecnico = "APROBADO"
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "modificado_en",
                    "estado_cupo",
                    "es_titular_activo",
                ]
            )
            return JsonResponse(
                {
                    "success": True,
                    "estado": leg.revision_tecnico,
                    "cupo_liberado": False,
                }
            )

        if accion == "RECHAZAR":
            leg.revision_tecnico = "RECHAZADO"
            leg.save(
                update_fields=[
                    "revision_tecnico",
                    "modificado_en",
                    "estado_cupo",
                    "es_titular_activo",
                ]
            )
            return JsonResponse(
                {"success": True, "estado": leg.revision_tecnico, "cupo_liberado": True}
            )

        # SUBSANAR
        motivo = (request.POST.get("motivo") or "").strip()
        if not motivo:
            return JsonResponse(
                {"success": False, "error": "Debe indicar un motivo de subsanación."},
                status=400,
            )

        leg.revision_tecnico = RevisionTecnico.SUBSANAR
        leg.subsanacion_motivo = motivo[:500]
        leg.subsanacion_solicitada_en = timezone.now()
        leg.subsanacion_usuario = user
        leg.save(
            update_fields=[
                "revision_tecnico",
                "subsanacion_motivo",
                "subsanacion_solicitada_en",
                "subsanacion_usuario",
                "modificado_en",
                "estado_cupo",
                "es_titular_activo",
            ]
        )

        return JsonResponse(
            {
                "success": True,
                "estado": str(RevisionTecnico.SUBSANAR),
                "cupo_liberado": True,
            }
        )
