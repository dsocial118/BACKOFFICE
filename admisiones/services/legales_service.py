from django.utils.http import url_has_allowed_host_and_scheme
from django.shortcuts import redirect
from django.contrib import messages
from django.db import models
from django.template.loader import render_to_string, get_template
from weasyprint import HTML
import os
from django.conf import settings
from django.db.models import Q
import logging
from io import BytesIO
import tempfile
from datetime import date

from django.core.files.base import ContentFile
from django.utils.html import strip_tags
from django.utils.text import slugify
from docx import Document
from htmldocx import HtmlToDocx
from .docx_service import DocumentTemplateService, TextFormatterService
from django.db import transaction
import unicodedata
import traceback

logger = logging.getLogger("django")

from admisiones.models.admisiones import (
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
    Admision,
    ArchivoAdmision,
    Documentacion,
    InformeTecnico,
    InformeComplementario,
)
from admisiones.forms.admisiones_forms import (
    LegalesNumIFForm,
    LegalesRectificarForm,
    ProyectoDisposicionForm,
    ProyectoConvenioForm,
    ConvenioNumIFFORM,
    DisposicionNumIFFORM,
    IntervencionJuridicosForm,
    InformeSGAForm,
    ConvenioForm,
    DisposicionForm,
    ReinicioExpedienteForm,
    SolicitarInformeComplementarioForm,
    DocumentosExpedienteForm,
)


def normalizar(texto):
    """Quita acentos y convierte a minúsculas para comparación segura."""
    if not texto:
        return ""
    texto = texto.strip().lower()
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    )
    return texto


class LegalesService:
    @staticmethod
    def _safe_redirect(request, admision):
        """Helper method for safe redirects"""
        if url_has_allowed_host_and_scheme(
            request.path_info, allowed_hosts={request.get_host()}
        ):
            return redirect(request.path_info)
        return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def _save_formulario_with_user(form, admision, request):
        """Helper to save formulario with user assignment"""
        instance = form.save(commit=False)
        instance.admision = admision
        if not getattr(instance, "creado_por", None) and request.user.is_authenticated:
            instance.creado_por = request.user
        instance.save()
        return instance

    @staticmethod
    def _reset_dictamen_flow(admision):
        """Reset flow based on dictamen type"""
        reset_fields = {
            "intervencion_juridicos": None,
            "rechazo_juridicos_motivo": None,
            "dictamen_motivo": None,
        }

        if admision.dictamen_motivo == "observacion en proyecto de convenio":
            FormularioProyectoDeConvenio.objects.filter(admision=admision).delete()
            FormularioProyectoDisposicion.objects.filter(admision=admision).delete()
            reset_fields["estado_legales"] = "Expediente Agregado"
        elif admision.dictamen_motivo == "observacion en proyecto de disposicion":
            FormularioProyectoDisposicion.objects.filter(admision=admision).delete()
            reset_fields["estado_legales"] = "IF Convenio Asignado"

        for field, value in reset_fields.items():
            setattr(admision, field, value)
        admision.save()

    @staticmethod
    def get_botones_disponibles(admision):
        """Retorna los botones que deben mostrarse según el estado actual"""
        botones = []

        puede_rectificar = not admision.legales_num_if

        formulario_proyecto = admision.admisiones_proyecto_convenio.first()
        formulario_reso = admision.admisiones_proyecto_disposicion.first()

        if admision.enviado_legales and admision.estado_legales == "Enviado a Legales":
            if puede_rectificar:
                botones.append("rectificar")
            if not admision.legales_num_if:
                botones.append("agregar_expediente")
            return botones

        if admision.estado_legales == "Expediente Agregado":
            botones.append("formulario_convenio")
        elif admision.estado_legales == "Formulario Convenio Creado":
            botones.append("if_convenio")
        elif admision.estado_legales == "IF Convenio Asignado":
            botones.append("formulario_disposicion")
        elif admision.estado_legales == "Formulario Disposición Creado":
            botones.append("if_disposicion")
        elif admision.estado_legales == "IF Disposición Asignado":
            botones.append("intervencion_juridicos")
        elif admision.estado_legales == "Juridicos: Rechazado":
            if admision.rechazo_juridicos_motivo == "providencia":
                botones.append("reinicio_expediente")
            elif admision.rechazo_juridicos_motivo == "dictamen":
                if admision.dictamen_motivo == "observacion en informe técnico":
                    if not admision.complementario_solicitado:
                        botones.append("informe_complementario")

        elif admision.estado_legales == "Informe Complementario Enviado":
            botones.append("revisar_informe_complementario")
        elif admision.estado_legales == "Informe Complementario: Validado":
            from admisiones.models.admisiones import InformeTecnicoComplementarioPDF

            pdf_complementario = InformeTecnicoComplementarioPDF.objects.filter(
                admision=admision
            ).first()

            if pdf_complementario and not pdf_complementario.numero_if:
                botones.append("if_informe_complementario")
            else:

                botones.append("formulario_convenio")

        elif admision.estado_legales in ["Rectificado", None]:
            if not admision.legales_num_if:
                botones.append("agregar_expediente")
            elif not formulario_proyecto:
                botones.append("formulario_convenio")
            elif formulario_proyecto and not formulario_proyecto.numero_if:
                botones.append("if_convenio")
            elif formulario_proyecto.numero_if and not formulario_reso:
                botones.append("formulario_disposicion")
            elif formulario_reso and not formulario_reso.numero_if:
                botones.append("if_disposicion")
            elif (
                formulario_proyecto.numero_if
                and formulario_reso.numero_if
                and not admision.intervencion_juridicos
            ):
                botones.append("intervencion_juridicos")

            if puede_rectificar and not formulario_proyecto and not formulario_reso:
                botones.append("rectificar")

        elif (
            admision.estado_legales == "Juridicos: Validado"
            and not admision.informe_sga
        ):
            botones.append("informe_sga")

        if admision.informe_sga and not admision.numero_convenio:
            botones.append("convenio")

        if admision.numero_convenio and not admision.numero_disposicion:
            botones.append("disposicion")

        if (
            not admision.enviada_a_archivo
            and not admision.dictamen_motivo
            and admision.rechazo_juridicos_motivo
            and admision.estado_legales != "Juridicos: Rechazado"
        ):
            botones.append("reinicio_expediente")

        if (
            admision.dictamen_motivo == "observacion en informe técnico"
            and not admision.complementario_solicitado
            and admision.estado_legales != "Juridicos: Rechazado"
        ):
            botones.append("informe_complementario")

        return botones

    @staticmethod
    def actualizar_estado_por_accion(admision, accion):
        """Actualiza el estado_legales basado en la acción realizada"""
        if accion == "intervencion_juridicos":
            if admision.intervencion_juridicos == "validado":
                admision.estado_legales = "Juridicos: Validado"
            elif admision.intervencion_juridicos == "rechazado":
                admision.estado_legales = "Juridicos: Rechazado"
        else:
            estados_por_accion = {
                "agregar_expediente": "Expediente Agregado",
                "formulario_convenio": "Formulario Convenio Creado",
                "if_convenio": "IF Convenio Asignado",
                "formulario_disposicion": "Formulario Disposición Creado",
                "if_disposicion": "IF Disposición Asignado",
                "informe_sga": "Informe SGA Generado",
                "convenio": "Convenio Firmado",
                "disposicion": "Acompañamiento Pendiente",
                "rectificar": "A Rectificar",
                "reinicio_expediente": "Archivado",
                "informe_complementario": "Informe Complementario Solicitado",
                "enviar_informe_complementario": "Informe Complementario Enviado",
            }

            if accion in estados_por_accion:
                admision.estado_legales = estados_por_accion[accion]

        admision.save(update_fields=["estado_legales"])

    @staticmethod
    def enviar_a_rectificar(request, admision):
        try:
            form = LegalesRectificarForm(request.POST)
            if form.is_valid():
                observaciones = form.cleaned_data["observaciones"]
                cambios = False

                if admision.estado_id != 3:
                    admision.estado_id = 3
                    cambios = True

                if admision.observaciones != observaciones:
                    admision.observaciones = observaciones
                    cambios = True

                if cambios:
                    admision.save()

                LegalesService.actualizar_estado_por_accion(admision, "rectificar")
                messages.success(request, "Enviado a rectificar con éxito.")
            else:
                messages.error(request, "Error al enviar a rectificar.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en enviar_a_rectificar",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al enviar a rectificar.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_legales_num_if(request, admision):
        try:
            form = LegalesNumIFForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()
                LegalesService.actualizar_estado_por_accion(
                    admision, "agregar_expediente"
                )
                messages.success(request, "Número de IF guardado correctamente.")
            else:
                messages.error(request, "Error al guardar el número de IF.")
            return LegalesService._safe_redirect(request, admision)
        except Exception:
            logger.exception(
                "Error en guardar_legales_num_if", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al guardar el número de IF.")
            return LegalesService._safe_redirect(request, admision)

    @staticmethod
    def guardar_intervencion_juridicos(request, admision):
        try:
            form = IntervencionJuridicosForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()

                if (
                    admision.intervencion_juridicos == "rechazado"
                    and admision.rechazo_juridicos_motivo == "dictamen"
                    and admision.dictamen_motivo
                    in [
                        "observacion en proyecto de convenio",
                        "observacion en proyecto de disposicion",
                    ]
                ):
                    LegalesService._reset_dictamen_flow(admision)
                else:
                    LegalesService.actualizar_estado_por_accion(
                        admision, "intervencion_juridicos"
                    )

                messages.success(
                    request, "Intervención Jurídicos guardada correctamente."
                )
            else:
                messages.error(request, "Error al guardar Intervención Jurídicos.")
        except Exception:
            logger.exception(
                "Error en guardar_intervencion_juridicos",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar Intervención Jurídicos."
            )
        return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_informe_sga(request, admision):
        try:
            admision.informe_sga = not admision.informe_sga
            admision.save(update_fields=["informe_sga"])
            if admision.informe_sga:
                LegalesService.actualizar_estado_por_accion(admision, "informe_sga")
            messages.success(
                request,
                f"Informe SGA {'Aceptado' if admision.informe_sga else 'No aceptado'}.",
            )
        except Exception:
            logger.exception(
                "Error en guardar_informe_sga", extra={"admision_pk": admision.pk}
            )
            messages.error(
                request, "Error inesperado al guardar el estado del Informe SGA."
            )
        return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_convenio(request, admision):
        try:
            form = ConvenioForm(request.POST, request.FILES, instance=admision)
            if form.is_valid():
                form.save()
                LegalesService.actualizar_estado_por_accion(admision, "convenio")
                messages.success(request, "Convenio guardado correctamente.")
            else:
                logger.error("Errores en ConvenioForm: %s", form.errors)
                messages.error(request, "Error al guardar el Convenio.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en guardar_convenio", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al guardar el Convenio.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_disposicion(request, admision):
        try:
            form = DisposicionForm(request.POST, request.FILES, instance=admision)
            if form.is_valid():
                form.save()
                LegalesService.actualizar_estado_por_accion(admision, "disposicion")
                messages.success(request, "Disposición guardada correctamente.")
            else:
                logger.error("Errores en DisposicionForm: %s", form.errors)
                messages.error(request, "Error al guardar Disposición.")
            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en guardar_disposicion", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al guardar Disposición.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_convenio_num_if(request, admision):
        try:
            formulario = (
                admision.admisiones_proyecto_convenio.first()
                or FormularioProyectoDeConvenio(admision=admision)
            )
            form = ConvenioNumIFFORM(request.POST, instance=formulario)
            if form.is_valid():
                LegalesService._save_formulario_with_user(form, admision, request)
                LegalesService.actualizar_estado_por_accion(admision, "if_convenio")
                messages.success(
                    request, "Número IF de Proyecto de Convenio guardado correctamente."
                )
            else:
                messages.error(
                    request, "Error al guardar el número IF de Proyecto de Convenio."
                )
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_convenio_num_if", extra={"admision_pk": admision.pk}
            )
            messages.error(
                request,
                "Error inesperado al guardar el número IF de Proyecto de Convenio.",
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_reinicio_expediente(request, admision):
        try:
            form = ReinicioExpedienteForm(request.POST, instance=admision)
            if form.is_valid():
                reinicio = form.save(commit=False)
                reinicio.enviada_a_archivo = True
                reinicio.save(
                    update_fields=[
                        "observaciones_reinicio_expediente",
                        "enviada_a_archivo",
                    ]
                )
                LegalesService.actualizar_estado_por_accion(
                    admision, "reinicio_expediente"
                )
                messages.success(
                    request,
                    "Reinicio de expediente guardado y enviado a archivo correctamente.",
                )
            else:
                messages.error(request, "Error al guardar el reinicio de expediente.")
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_reinicio_expediente",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar el reinicio de expediente."
            )
            return redirect(request.path_info)

    @staticmethod
    def revisar_informe_complementario(request, admision):
        try:
            informe_complementario = InformeComplementario.objects.filter(
                admision=admision, estado="enviado_validacion"
            ).first()

            if not informe_complementario:
                messages.error(
                    request, "No se encontró informe complementario para revisar."
                )
                return redirect(request.path_info)

            accion = request.POST.get("accion_complementario")
            observaciones = request.POST.get("observaciones_complementario", "")

            if accion == "validar":
                informe_complementario.estado = "validado"
                informe_complementario.save()

                from admisiones.services.informes_service import InformeService

                pdf_final = InformeService.generar_y_guardar_pdf_complementario(
                    informe_complementario
                )

                if pdf_final:

                    admision.estado_legales = "Informe Complementario: Validado"
                    admision.save(update_fields=["estado_legales"])
                    messages.success(
                        request,
                        "Informe complementario validado correctamente. Se ha generado el PDF final.",
                    )
                else:
                    messages.error(
                        request,
                        "Error al generar el PDF final del informe complementario.",
                    )

            elif accion == "rectificar":
                if not observaciones.strip():
                    messages.error(
                        request, "Las observaciones son obligatorias para rectificar."
                    )
                    return redirect(request.path_info)

                informe_complementario.estado = "rectificar"
                informe_complementario.observaciones_legales = observaciones
                informe_complementario.save()
                admision.estado_legales = "Informe Complementario Solicitado"
                admision.save(update_fields=["estado_legales"])
                messages.success(
                    request, "Informe complementario enviado a rectificar."
                )
            else:
                messages.error(request, "Acción no válida.")
                return redirect(request.path_info)

            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en revisar_informe_complementario",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al revisar informe complementario."
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_if_informe_complementario(request, admision):
        try:
            numero_if = request.POST.get("numero_if_complementario", "").strip()
            if not numero_if:
                messages.error(request, "El número IF es obligatorio.")
                return redirect(request.path_info)

            from admisiones.models.admisiones import InformeTecnicoComplementarioPDF

            pdf_complementario = InformeTecnicoComplementarioPDF.objects.filter(
                admision=admision
            ).first()

            if pdf_complementario:
                pdf_complementario.numero_if = numero_if
                pdf_complementario.save()

                LegalesService._limpiar_flujo_anterior(admision)

                messages.success(
                    request,
                    "Número IF del informe complementario guardado correctamente.",
                )
            else:
                messages.error(
                    request, "No se encontró PDF de informe complementario validado."
                )

            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_if_informe_complementario",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al guardar IF del informe complementario."
            )
            return redirect(request.path_info)

    @staticmethod
    def _limpiar_flujo_anterior(admision):
        """Limpia los datos del flujo anterior para reiniciar desde formulario convenio"""
        try:

            FormularioProyectoDeConvenio.objects.filter(admision=admision).delete()
            FormularioProyectoDisposicion.objects.filter(admision=admision).delete()

            admision.intervencion_juridicos = None
            admision.rechazo_juridicos_motivo = None
            admision.dictamen_motivo = None
            admision.complementario_solicitado = False
            admision.observaciones_informe_tecnico_complementario = None

            admision.estado_legales = "Informe Complementario: Validado"
            admision.save(
                update_fields=[
                    "intervencion_juridicos",
                    "rechazo_juridicos_motivo",
                    "dictamen_motivo",
                    "complementario_solicitado",
                    "observaciones_informe_tecnico_complementario",
                    "estado_legales",
                ]
            )

        except Exception:
            logger.exception(
                "Error en _limpiar_flujo_anterior",
                extra={"admision_pk": admision.pk},
            )

    @staticmethod
    def guardar_observaciones_informe_complementario(request, admision):
        try:
            form = SolicitarInformeComplementarioForm(request.POST, instance=admision)
            if form.is_valid():
                complementario = form.save(commit=False)
                complementario.complementario_solicitado = True
                complementario.save(
                    update_fields=[
                        "observaciones_informe_tecnico_complementario",
                        "complementario_solicitado",
                    ]
                )
                LegalesService.actualizar_estado_por_accion(
                    admision, "informe_complementario"
                )
                messages.success(request, "Informe complementario solicitado.")
            else:
                messages.error(request, "Error al solicitar informe complementario.")
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_observaciones_informe_complementario",
                extra={"admision_pk": admision.pk},
            )
            messages.error(
                request, "Error inesperado al solicitar informe complementario."
            )
            return redirect(request.path_info)

    @staticmethod
    def guardar_dispo_num_if(request, admision):
        try:
            formulario = (
                admision.admisiones_proyecto_disposicion.first()
                or FormularioProyectoDisposicion(admision=admision)
            )
            form = DisposicionNumIFFORM(request.POST, instance=formulario)
            if form.is_valid():
                LegalesService._save_formulario_with_user(form, admision, request)
                LegalesService.actualizar_estado_por_accion(admision, "if_disposicion")
                messages.success(
                    request,
                    "Número IF de Proyecto de Disposición guardado correctamente.",
                )
            else:
                messages.error(
                    request, "Error al guardar el número IF de Proyecto de Disposición."
                )
            return redirect(request.path_info)
        except Exception:
            logger.exception(
                "Error en guardar_dispo_num_if", extra={"admision_pk": admision.pk}
            )
            messages.error(
                request,
                "Error inesperado al guardar el número IF de Proyecto de Disposición.",
            )
            return redirect(request.path_info)

    @staticmethod
    def validar_juridicos(request, admision):
        try:
            reso_completo = FormularioProyectoDisposicion.objects.filter(
                admision=admision
            ).exists()
            proyecto_completo = FormularioProyectoDeConvenio.objects.filter(
                admision=admision
            ).exists()

            condiciones_validas = (
                reso_completo
                and proyecto_completo
                and not (admision.observaciones and admision.observaciones.strip())
                and admision.estado_legales != "A Rectificar"
                and admision.legales_num_if
            )

            if condiciones_validas:
                admision.estado_legales = "Pendiente de Validacion"
                admision.save()
                messages.success(
                    request, "Estado cambiado a 'Pendiente de Validacion'."
                )
            else:
                messages.error(
                    request,
                    "No se puede validar: asegúrese de completar ambos formularios y agregar el Número IF.",
                )

            return LegalesService._safe_redirect(request, admision)
        except Exception:
            logger.exception(
                "Error en validar_juridicos", extra={"admision_pk": admision.pk}
            )
            messages.error(request, "Error inesperado al validar jurídicos.")
            return LegalesService._safe_redirect(request, admision)

    @staticmethod
    def guardar_formulario_reso(request, admision):
        try:
            with transaction.atomic():
                formulario_existente = FormularioProyectoDisposicion.objects.filter(
                    admision=admision
                ).first()
                form = ProyectoDisposicionForm(
                    request.POST, instance=formulario_existente
                )

                if not form.is_valid():
                    messages.error(
                        request, "Error al guardar el Formulario Proyecto Disposición."
                    )
                    return redirect("admisiones_legales_ver", pk=admision.pk)

                nuevo_formulario = form.save(commit=False)
                nuevo_formulario.admision = admision
                nuevo_formulario.tipo = admision.tipo
                if request.user.is_authenticated:
                    nuevo_formulario.creado_por = request.user
                nuevo_formulario.save()

                informe = (
                    InformeTecnico.objects.filter(admision=admision)
                    .order_by("-id")
                    .first()
                )

                proyecto_convenio = admision.admisiones_proyecto_convenio.first()
                proyecto_disposicion_if = FormularioProyectoDeConvenio.objects.filter(
                    admision=admision
                ).first()

                context = {
                    "admision": admision,
                    "formulario": nuevo_formulario,
                    "informe": informe,
                    "proyecto_convenio": proyecto_convenio,
                    "proyecto_disposicion_if": proyecto_disposicion_if.numero_if,
                }

                tipo_admision = admision.tipo or "incorporacion"

                pdf_template_name = (
                    f"admisiones/pdf/{tipo_admision}_pdf_proyecto_disposicion.html"
                )
                docx_template_name = f"{tipo_admision}_docx_proyecto_disposicion.docx"

                html_pdf = render_to_string(pdf_template_name, context)
                if not html_pdf.strip():
                    raise ValueError(
                        f"El template {pdf_template_name} devolvió contenido vacío."
                    )

                base_url = str(
                    getattr(settings, "STATIC_ROOT", "")
                    or getattr(settings, "BASE_DIR", "")
                    or "."
                )
                pdf_bytes = HTML(string=html_pdf, base_url=base_url).write_pdf()
                if not pdf_bytes:
                    raise ValueError(
                        "WeasyPrint no devolvió contenido para el PDF generado."
                    )
                pdf_content = ContentFile(pdf_bytes)

                docx_content = DocumentTemplateService.generar_docx(
                    template_name=docx_template_name,
                    context=context,
                    app_name="admisiones",
                )

                if not docx_content:
                    raise ValueError("El servicio de generación de DOCX devolvió None.")

                nombre_comedor = (
                    admision.comedor.nombre
                    if getattr(admision.comedor, "nombre", None)
                    else "sin-nombre"
                )
                fecha_actual = date.today().strftime("%Y-%m-%d")
                base_filename = (
                    slugify(f"disposicion-{nombre_comedor}-{fecha_actual}")
                    or f"disposicion-{fecha_actual}"
                )

                if nuevo_formulario.archivo:
                    nuevo_formulario.archivo.delete(save=False)
                nuevo_formulario.archivo.save(
                    f"{base_filename}.pdf", pdf_content, save=False
                )

                if nuevo_formulario.archivo_docx:
                    nuevo_formulario.archivo_docx.delete(save=False)
                nuevo_formulario.archivo_docx.save(
                    f"{base_filename}.docx", docx_content, save=False
                )

                nuevo_formulario.save(update_fields=["archivo", "archivo_docx"])

                LegalesService.actualizar_estado_por_accion(
                    admision, "formulario_disposicion"
                )

                messages.success(
                    request, "Formulario guardado y documentos generados correctamente."
                )
                return redirect("admisiones_legales_ver", pk=admision.pk)

        except Exception as e:
            logger.exception(
                "Error en guardar_formulario_reso",
                extra={"admision_pk": admision.pk, "error": str(e)},
            )
            messages.error(
                request,
                f"❌ Error inesperado al guardar el Formulario Proyecto Disposición: {str(e)}",
            )
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def guardar_formulario_proyecto_convenio(request, admision):
        try:
            with transaction.atomic():
                formulario_existente = FormularioProyectoDeConvenio.objects.filter(
                    admision=admision
                ).first()
                form = ProyectoConvenioForm(request.POST, instance=formulario_existente)

                if not form.is_valid():
                    messages.error(
                        request, "Error al guardar el formulario Proyecto de Convenio."
                    )
                    return redirect(request.path_info)

                nuevo_formulario = form.save(commit=False)
                nuevo_formulario.admision = admision
                if request.user.is_authenticated:
                    nuevo_formulario.creado_por = request.user
                nuevo_formulario.save()

                informe = (
                    InformeTecnico.objects.filter(admision=admision)
                    .order_by("-id")
                    .first()
                )

                context = {
                    "admision": admision,
                    "formulario": nuevo_formulario,
                    "informe": informe,
                }

                tipo_admision = admision.tipo or "incorporacion"
                tipo_convenio = normalizar(
                    admision.tipo_convenio.nombre if admision.tipo_convenio else ""
                )

                if "base" in tipo_convenio:
                    convenio_suffix = "base"
                elif "eclesi" in tipo_convenio:
                    convenio_suffix = "juridica_eclesiastica"
                elif "juridica" in tipo_convenio:
                    convenio_suffix = "juridica"
                else:
                    raise ValueError(
                        f"Tipo de convenio no reconocido: '{admision.tipo_convenio.nombre}'"
                    )

                pdf_template_name = f"admisiones/pdf/{tipo_admision}_pdf_proyecto_convenio_{convenio_suffix}.html"
                docx_template_name = (
                    f"{tipo_admision}_docx_proyecto_convenio_{convenio_suffix}.docx"
                )

                html_pdf = render_to_string(pdf_template_name, context)
                if not html_pdf.strip():
                    raise ValueError(
                        f"El template {pdf_template_name} devolvió contenido vacío."
                    )

                base_url = str(
                    getattr(settings, "STATIC_ROOT", "")
                    or getattr(settings, "BASE_DIR", "")
                    or "."
                )
                pdf_bytes = HTML(string=html_pdf, base_url=base_url).write_pdf()
                if not pdf_bytes:
                    raise ValueError(
                        "WeasyPrint no devolvió contenido para el PDF generado."
                    )
                pdf_content = ContentFile(pdf_bytes)

                docx_content = DocumentTemplateService.generar_docx(
                    template_name=docx_template_name,
                    context=context,
                    app_name="admisiones",
                )

                if not docx_content:
                    raise ValueError("El servicio de generación de DOCX devolvió None.")

                nombre_comedor = (
                    admision.comedor.nombre
                    if getattr(admision.comedor, "nombre", None)
                    else "sin-nombre"
                )
                fecha_actual = date.today().strftime("%Y-%m-%d")
                base_filename = (
                    slugify(f"convenio-{nombre_comedor}-{fecha_actual}")
                    or f"convenio-{fecha_actual}"
                )

                if nuevo_formulario.archivo:
                    nuevo_formulario.archivo.delete(save=False)
                nuevo_formulario.archivo.save(
                    f"{base_filename}.pdf", pdf_content, save=False
                )

                if nuevo_formulario.archivo_docx:
                    nuevo_formulario.archivo_docx.delete(save=False)
                nuevo_formulario.archivo_docx.save(
                    f"{base_filename}.docx", docx_content, save=False
                )

                nuevo_formulario.save(update_fields=["archivo", "archivo_docx"])

                LegalesService.actualizar_estado_por_accion(
                    admision, "formulario_convenio"
                )

                messages.success(
                    request,
                    "Formulario guardado y documentos generados correctamente.",
                )
                return redirect(request.path_info)

        except Exception as e:
            logger.exception(
                "Error en guardar_formulario_proyecto_convenio",
                extra={"admision_pk": admision.pk, "error": str(e)},
            )
            messages.error(
                request,
                f"❌ Error inesperado al guardar el formulario Proyecto de Convenio: {str(e)}",
            )
            return redirect(request.path_info)

    @staticmethod
    def get_admisiones_legales_filtradas(query=""):
        try:
            queryset = Admision.objects.filter(enviado_legales=True).select_related(
                "comedor", "tipo_convenio"
            )

            if query:
                query = query.strip().lower()
                queryset = queryset.filter(
                    Q(comedor__nombre__icontains=query)
                    | Q(tipo_convenio__nombre__icontains=query)
                    | Q(num_expediente__icontains=query)
                    | Q(num_if__icontains=query)
                    | Q(estado_legales__icontains=query)
                )

            return queryset
        except Exception:
            logger.exception("Error en get_admisiones_legales_filtradas")
            return Admision.objects.none()

    @staticmethod
    def procesar_post_legales(request, admision):
        try:
            if "btnLegalesNumIF" in request.POST:
                return LegalesService.guardar_legales_num_if(request, admision)

            if "BtnIntervencionJuridicos" in request.POST:
                return LegalesService.guardar_intervencion_juridicos(request, admision)

            if "BtnInformeSGA" in request.POST:
                return LegalesService.guardar_informe_sga(request, admision)

            if "btnConvenio" in request.POST:
                return LegalesService.guardar_convenio(request, admision)

            if "btnDisposicion" in request.POST:
                return LegalesService.guardar_disposicion(request, admision)

            if "btnConvenioNumIF" in request.POST:
                return LegalesService.guardar_convenio_num_if(request, admision)

            if "btnDispoNumIF" in request.POST:
                return LegalesService.guardar_dispo_num_if(request, admision)

            if "btnReinicioExpediente" in request.POST:
                return LegalesService.guardar_reinicio_expediente(request, admision)

            if "btnInformeComplementario" in request.POST:
                return LegalesService.guardar_observaciones_informe_complementario(
                    request, admision
                )

            if "btnRevisarInformeComplementario" in request.POST:
                return LegalesService.revisar_informe_complementario(request, admision)

            if "btnIFInformeComplementario" in request.POST:
                return LegalesService.guardar_if_informe_complementario(
                    request, admision
                )

            if "ValidacionJuridicos" in request.POST:
                return LegalesService.validar_juridicos(request, admision)

            if "btnRESO" in request.POST:
                return LegalesService.guardar_formulario_reso(request, admision)

            if "btnProyectoConvenio" in request.POST:
                return LegalesService.guardar_formulario_proyecto_convenio(
                    request, admision
                )

            if "btnObservaciones" in request.POST:
                return LegalesService.enviar_a_rectificar(request, admision)

            return redirect("admisiones_legales_ver", pk=admision.pk)
        except Exception:
            logger.exception(
                "Error en procesar_post_legales",
                extra={"admision_pk": admision.pk},
            )
            messages.error(request, "Error inesperado al procesar el POST de legales.")
            return redirect("admisiones_legales_ver", pk=admision.pk)

    @staticmethod
    def get_legales_context(admision, request=None):
        try:
            documentaciones = Documentacion.objects.filter(
                models.Q(convenios=admision.tipo_convenio)
            ).distinct()
            informe = LegalesService.get_informe_por_tipo_convenio(admision)
            archivos_subidos = ArchivoAdmision.objects.filter(admision=admision)
            informes_complementarios = InformeComplementario.objects.filter(
                admision=admision
            ).order_by("-creado")

            from admisiones.models.admisiones import InformeTecnicoComplementarioPDF

            pdf_complementario_final = InformeTecnicoComplementarioPDF.objects.filter(
                admision=admision
            ).first()
            from django.core.paginator import Paginator

            historial_queryset = admision.historial.all().order_by("-fecha")
            paginator = Paginator(historial_queryset, 10)
            page_number = request.GET.get("historial_page", 1) if request else 1
            historial_page = paginator.get_page(page_number)

            # Preparar datos para el componente data_table
            historial_headers = [
                {"title": "Fecha", "width": "20%"},
                {"title": "Campo", "width": "25%"},
                {"title": "Valor", "width": "35%"},
                {"title": "Usuario", "width": "20%"},
            ]

            # Formatear datos del historial para el componente
            historial_cambios = []
            for cambio in historial_page:
                valor_formateado = cambio.valor_nuevo
                if valor_formateado == "True":
                    valor_formateado = "Si"
                elif valor_formateado == "False":
                    valor_formateado = "No"
                elif not valor_formateado:
                    valor_formateado = "-"

                historial_cambios.append(
                    {
                        "cells": [
                            {"content": cambio.fecha.strftime("%d/%m/%Y %H:%M")},
                            {"content": cambio.campo},
                            {"content": valor_formateado},
                            {
                                "content": (
                                    cambio.usuario.username if cambio.usuario else "-"
                                )
                            },
                        ]
                    }
                )

            archivos_dict = {}
            documentos_personalizados = []
            for archivo in archivos_subidos:
                if getattr(archivo, "documentacion_id", None):
                    archivos_dict[archivo.documentacion_id] = archivo
                else:
                    documentos_personalizados.append(
                        {
                            "id": archivo.id,
                            "nombre": archivo.nombre_personalizado
                            or "Documento adicional",
                            "archivo_url": (
                                archivo.archivo.url if archivo.archivo else None
                            ),
                        }
                    )

            documentos_info = [
                {
                    "id": doc.id,
                    "nombre": doc.nombre,
                    "archivo_url": (
                        archivos_dict[doc.id].archivo.url
                        if doc.id in archivos_dict
                        else None
                    ),
                }
                for doc in documentaciones
            ]

            documentos_info.extend(documentos_personalizados)

            reso_formulario = admision.admisiones_proyecto_disposicion.first()
            proyecto_formulario = admision.admisiones_proyecto_convenio.first()

            if reso_formulario:
                reso_form = ProyectoDisposicionForm(instance=reso_formulario)
                dispo_num_if_form = DisposicionNumIFFORM(instance=reso_formulario)
            else:
                reso_form = ProyectoDisposicionForm()
                dispo_num_if_form = DisposicionNumIFFORM()

            if proyecto_formulario:
                proyecto_form = ProyectoConvenioForm(instance=proyecto_formulario)
                convenio_num_if_form = ConvenioNumIFFORM(instance=proyecto_formulario)
            else:
                proyecto_form = ProyectoConvenioForm()
                convenio_num_if_form = ConvenioNumIFFORM()

            legales_num_if_form = LegalesNumIFForm(instance=admision)

            documentos_expediente = DocumentosExpediente.objects.filter(
                admision=admision
            )

            tipos = ["Informe SGA", "Disposición", "Firma Convenio", "Numero CONV"]

            ultimos_valores = {}
            for tipo in tipos:
                ultimo_doc = (
                    documentos_expediente.filter(tipo=tipo).order_by("-creado").first()
                )
                ultimos_valores[tipo] = ultimo_doc.value if ultimo_doc else None

            return {
                "documentos": documentos_info,
                "informe": informe,
                "historial_cambios": historial_cambios,
                "historial_headers": historial_headers,
                "historial_page_obj": historial_page,
                "historial_is_paginated": historial_page.has_other_pages(),
                "historial_page_param": "historial_page",
                "pdf_url": (
                    getattr(admision, "informe_pdf", None).archivo.url
                    if getattr(admision, "informe_pdf", None)
                    and getattr(admision.informe_pdf, "archivo", None)
                    else None
                ),
                "formulario_reso": reso_formulario,
                "formulario_reso_completo": bool(reso_formulario),
                "formulario_proyecto": proyecto_formulario,
                "formulario_proyecto_completo": bool(proyecto_formulario),
                "reso_form": reso_form,
                "proyecto_form": proyecto_form,
                "form_legales_num_if": legales_num_if_form,
                "documentos_form": DocumentosExpedienteForm(),
                "convenio_num_if": convenio_num_if_form,
                "dispo_num_if": dispo_num_if_form,
                "documentos_form": DocumentosExpedienteForm(),
                "form_intervencion_juridicos": IntervencionJuridicosForm(
                    instance=admision
                ),
                "form_informe_sga": InformeSGAForm(instance=admision),
                "form_convenio": ConvenioForm(instance=admision),
                "form_disposicion": DisposicionForm(instance=admision),
                "form_reinicio_expediente": ReinicioExpedienteForm(instance=admision),
                "form_solicitar_informe_complementario": SolicitarInformeComplementarioForm(
                    instance=admision
                ),
                "value_informe_sga": ultimos_valores["Informe SGA"],
                "value_disposicion": ultimos_valores["Disposición"],
                "value_firma_convenio": ultimos_valores["Firma Convenio"],
                "value_numero_conv": ultimos_valores["Numero CONV"],
                "informes_complementarios": informes_complementarios,
                "pdf_complementario_final": pdf_complementario_final,
                "botones_disponibles": LegalesService.get_botones_disponibles(admision),
            }
        except Exception:
            logger.exception(
                "Error en get_legales_context",
                extra={"admision_pk": admision.pk},
            )
            return {}

    @staticmethod
    def get_informe_por_tipo_convenio(admision):
        try:
            tipo = admision.tipo_informe
            if not tipo:
                return None
            return InformeTecnico.objects.filter(admision=admision, tipo=tipo).first()
        except Exception:
            logger.exception(
                "Error en get_informe_por_tipo_convenio",
                extra={"admision_pk": admision.pk},
            )
            return None

    @staticmethod
    def generar_documento_convenio(admision, template_name="proyecto_convenio.docx"):
        """Genera documento DOCX de proyecto de convenio usando template"""
        try:
            context = TextFormatterService.preparar_contexto_proyecto_convenio(admision)
            docx_buffer = DocumentTemplateService.generar_docx(template_name, context)

            if docx_buffer:
                filename = f"proyecto_convenio_{admision.id}.docx"
                return ContentFile(docx_buffer.getvalue(), name=filename)

            return None
        except Exception:
            logger.exception(
                "Error en generar_documento_convenio",
                extra={"admision_id": admision.id, "template": template_name},
            )
            return None

    @staticmethod
    def generar_documento_disposicion(
        admision, template_name="proyecto_disposicion.docx"
    ):
        """Genera documento DOCX de proyecto de disposición usando template"""
        try:
            context = TextFormatterService.preparar_contexto_proyecto_disposicion(
                admision
            )
            docx_buffer = DocumentTemplateService.generar_docx(template_name, context)

            if docx_buffer:
                filename = f"proyecto_disposicion_{admision.id}.docx"
                return ContentFile(docx_buffer.getvalue(), name=filename)

            return None
        except Exception:
            logger.exception(
                "Error en generar_documento_disposicion",
                extra={"admision_id": admision.id, "template": template_name},
            )
            return None
