import os
from typing import Any
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models.base import Model
from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    TemplateView,
)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST


from comedores.forms.relevamiento_form import PuntosEntregaForm
from comedores.models.relevamiento import Relevamiento, ClasificacionComedor
from comedores.forms.comedor_form import (
    ComedorForm,
    ReferenteForm,
    NominaForm,
)
from comedores.forms.observacion_form import ObservacionForm
from comedores.forms.relevamiento_form import (
    AnexoForm,
    ColaboradoresForm,
    EspacioCocinaForm,
    EspacioForm,
    EspacioPrestacionForm,
    FuenteComprasForm,
    FuenteRecursosForm,
    FuncionamientoPrestacionForm,
    PrestacionForm,
    RelevamientoForm,
)
from comedores.models.comedor import (
    Comedor,
    DocumentoRendicionFinal,
    EstadoDocumentoRendicionFinal,
    ImagenComedor,
    Observacion,
    Nomina,
    RendicionCuentasFinal,
)

from admisiones.models.admisiones import (
    Admision,
    InformeTecnicoBase,
    InformeTecnicoJuridico,
)
from comedores.models.relevamiento import Prestacion
from comedores.services.comedor_service import ComedorService
from comedores.services.relevamiento_service import RelevamientoService

from comedores.services.rendicion_cuentas_final_service import (
    RendicionCuentasFinalService,
)
from duplas.dupla_service import DuplaService
from historial.services.historial_service import HistorialService


@method_decorator(csrf_exempt, name="dispatch")  # FIXME: No exceptuar nunca csrf
class NominaDetailView(TemplateView):
    template_name = "comedor/nomina_detail.html"
    model = Nomina

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        (
            nomina,
            cantidad_nomina_m,
            cantidad_nomina_f,
            espera,
            cantidad_intervenciones,
        ) = ComedorService.detalle_de_nomina(self.kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        context["nomina"] = nomina
        context["nominaM"] = cantidad_nomina_m
        context["nominaF"] = cantidad_nomina_f
        context["espera"] = espera
        context["object"] = comedor
        context["cantidad_nomina"] = cantidad_intervenciones

        return context


class NominaCreateView(CreateView):
    model = Nomina
    template_name = "comedor/nomina_form.html"
    form_class = NominaForm

    def form_valid(self, form):
        pk = self.kwargs["pk"]
        form.save()
        return redirect("nomina_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])

        context["form"] = self.get_form()
        context["object"] = comedor

        return context


class NominaDeleteView(DeleteView):
    model = Nomina
    template_name = "comedor/nomina_confirm_delete.html"

    def form_valid(self, form):
        self.object.delete()
        return redirect("nomina_ver", pk=self.kwargs["pk2"])


class NominaUpdateView(UpdateView):
    model = Nomina
    form_class = NominaForm
    template_name = "comedor/nomina_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("nomina_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = comedor
        return context


class ComedorListView(ListView):
    model = Comedor
    template_name = "comedor/comedor_list.html"
    context_object_name = "comedores"
    paginate_by = 10

    def get_queryset(self):
        query = self.request.GET.get("busqueda")
        return ComedorService.get_comedores_filtrados(query)


class ComedorCreateView(CreateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["referente_form"] = ReferenteForm(
            self.request.POST or None, prefix="referente"
        )
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")

        if referente_form.is_valid():  # Creo y asigno el referente
            self.object = form.save(commit=False)
            self.object.referente = referente_form.save()
            self.object.save()
            for imagen in imagenes:  # Creo las imágenes
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDetailView(DetailView):
    model = Comedor
    template_name = "comedor/comedor_detail.html"
    context_object_name = "comedor"

    def get_object(self, queryset=None):
        return ComedorService.get_comedor_detail_object(self.kwargs["pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
        ) = ComedorService.get_presupuestos(self.object["id"])

        context.update(
            {
                "relevamientos": Relevamiento.objects.filter(comedor=self.object["id"])
                .values("id", "fecha_visita", "estado")
                .order_by("-estado", "-id")[:1],
                "observaciones": Observacion.objects.filter(comedor=self.object["id"])
                .values("id", "fecha_visita")
                .order_by("-fecha_visita")[:3],
                "count_relevamientos": Relevamiento.objects.filter(
                    comedor=self.object["id"]
                ).count(),
                "count_beneficiarios": count_beneficiarios,
                "presupuesto_desayuno": valor_desayuno,
                "presupuesto_almuerzo": valor_almuerzo,
                "presupuesto_merienda": valor_merienda,
                "presupuesto_cena": valor_cena,
                "imagenes": ImagenComedor.objects.filter(
                    comedor=self.object["id"]
                ).values("imagen"),
                "comedor_categoria": ClasificacionComedor.objects.filter(
                    comedor=self.object["id"]
                )
                .order_by("-fecha")
                .first(),
                "GESTIONAR_API_KEY": os.getenv("GESTIONAR_API_KEY"),
                "GESTIONAR_API_CREAR_COMEDOR": os.getenv("GESTIONAR_API_CREAR_COMEDOR"),
            }
        )

        admision = Admision.objects.filter(comedor=self.object["id"]).first()

        context["admision"] = admision
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        is_new_relevamiento = "territorial" in request.POST
        is_edit_relevamiento = "territorial_editar" in request.POST

        if is_new_relevamiento or is_edit_relevamiento:
            try:
                relevamiento = None
                if is_new_relevamiento:
                    relevamiento = RelevamientoService.create_pendiente(
                        request, self.object["id"]
                    )

                elif is_edit_relevamiento:
                    relevamiento = RelevamientoService.update_territorial(request)

                return redirect(
                    reverse(
                        "relevamiento_detalle",
                        kwargs={
                            "pk": relevamiento.pk,
                            "comedor_pk": relevamiento.comedor.pk,
                        },
                    )
                )
            except Exception as e:
                messages.error(request, f"Error al crear el relevamiento: {e}")
                return redirect("comedor_detalle", pk=self.object["id"])


class AsignarDuplaListView(ListView):  # FIXME: Por que esto es una ListView?
    model = Comedor
    template_name = "comedor/asignar_dupla_form.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        duplas = DuplaService.get_duplas_by_estado_activo()
        data["comedor"] = comedor
        data["duplas"] = duplas
        return data

    def post(self, request, *args, **kwargs):
        dupla_id = request.POST.get("dupla_id")
        comedor_id = self.kwargs["pk"]

        if dupla_id:
            try:
                ComedorService.asignar_dupla_a_comedor(dupla_id, comedor_id)
                messages.success(request, "Dupla asignada correctamente.")
            except Exception as e:
                messages.error(request, f"Error al asignar la dupla: {e}")
        else:
            messages.error(request, "No se seleccionó ninguna dupla.")

        return redirect("comedor_detalle", pk=comedor_id)


class ComedorUpdateView(UpdateView):
    model = Comedor
    form_class = ComedorForm
    template_name = "comedor/comedor_form.html"

    def get_success_url(self):
        return reverse("comedor_detalle", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        self.object = self.get_object()
        data["referente_form"] = ReferenteForm(
            self.request.POST if self.request.POST else None,
            instance=self.object.referente,
            prefix="referente",
        )
        data["imagenes_borrar"] = ImagenComedor.objects.filter(
            comedor=self.object.pk
        ).values("id", "imagen")
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        referente_form = context["referente_form"]
        imagenes = self.request.FILES.getlist("imagenes")

        if referente_form.is_valid():  # Creo y asigno el referente
            self.object = form.save()
            self.object.referente = referente_form.save()
            self.object.save()

            ComedorService.borrar_imagenes(self.request.POST)  # Borro las imagenes

            for imagen in imagenes:  # Creo las imagenes
                try:
                    ComedorService.create_imagenes(imagen, self.object.pk)
                except Exception:
                    return self.form_invalid(form)

            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class ComedorDeleteView(DeleteView):
    model = Comedor
    template_name = "comedor/comedor_confirm_delete.html"
    context_object_name = "comedor"
    success_url = reverse_lazy("comedores")


class RelevamientoListView(ListView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_list.html"
    context_object_name = "relevamientos"

    def get_queryset(self):
        comedor = self.kwargs["comedor_pk"]
        return (
            Relevamiento.objects.filter(comedor=comedor)
            .order_by("-estado", "-id")
            .values("id", "fecha_visita", "estado")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comedor"] = Comedor.objects.values(
            "id",
            "nombre",
            "provincia__nombre",
            "localidad__nombre",
            "municipio__nombre",
        ).get(pk=self.kwargs["comedor_pk"])

        return context


class RelevamientoCreateView(CreateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento/relevamiento_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = {
            "funcionamiento_form": FuncionamientoPrestacionForm,
            "espacio_form": EspacioForm,
            "espacio_cocina_form": EspacioCocinaForm,
            "espacio_prestacion_form": EspacioPrestacionForm,
            "colaboradores_form": ColaboradoresForm,
            "recursos_form": FuenteRecursosForm,
            "compras_form": FuenteComprasForm,
            "prestacion_form": PrestacionForm,
            "referente_form": ReferenteForm,
            "anexo_form": AnexoForm,
            "punto_entregas_form": PuntosEntregaForm,
        }

        for form_name, form_class in forms.items():
            data[form_name] = form_class(
                self.request.POST if self.request.POST else None
            )

        data["comedor"] = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {
            "funcionamiento_form": context["funcionamiento_form"],
            "espacio_form": context["espacio_form"],
            "espacio_cocina_form": context["espacio_cocina_form"],
            "espacio_prestacion_form": context["espacio_prestacion_form"],
            "colaboradores_form": context["colaboradores_form"],
            "recursos_form": context["recursos_form"],
            "compras_form": context["compras_form"],
            "prestacion_form": context["prestacion_form"],
            "referente_form": context["referente_form"],
            "anexo_form": context["anexo_form"],
        }

        if all(form.is_valid() for form in forms.values()):
            self.object = RelevamientoService.populate_relevamiento(form, forms)

            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
            return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDetailView(DetailView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_detail.html"
    context_object_name = "relevamiento"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        relevamiento = Relevamiento.objects.get(pk=self.get_object()["id"])
        context["relevamiento"]["gas"] = (
            RelevamientoService.separate_string(
                relevamiento.espacio.cocina.abastecimiento_combustible.all()
            )
            if relevamiento.espacio
            else None
        )
        context["prestacion"] = (
            Prestacion.objects.get(pk=relevamiento.prestacion.id)
            if relevamiento.prestacion
            else None
        )
        context["relevamiento"]["donaciones"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_donaciones_particulares.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["nacional"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_nacional.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["provincial"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_provincial.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["municipal"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_estado_municipal.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["otras"] = (
            RelevamientoService.separate_string(
                relevamiento.recursos.recursos_otros.all()
            )
            if relevamiento.recursos
            else None
        )

        context["relevamiento"]["Entregas"] = (
            RelevamientoService.separate_string(
                relevamiento.punto_entregas.frecuencia_recepcion_mercaderias.all()
            )
            if relevamiento.punto_entregas
            else None
        )

        return context

    def get_object(self, queryset=None):
        return RelevamientoService.get_relevamiento_detail_object(self.kwargs["pk"])


class RelevamientoUpdateView(UpdateView):
    model = Relevamiento
    form_class = RelevamientoForm
    template_name = "relevamiento/relevamiento_form.html"
    success_url = reverse_lazy("relevamiento_lista")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["comedor_pk"] = self.kwargs["comedor_pk"]
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        forms = {
            "funcionamiento_form": FuncionamientoPrestacionForm,
            "espacio_form": EspacioForm,
            "espacio_cocina_form": EspacioCocinaForm,
            "espacio_prestacion_form": EspacioPrestacionForm,
            "colaboradores_form": ColaboradoresForm,
            "recursos_form": FuenteRecursosForm,
            "compras_form": FuenteComprasForm,
            "prestacion_form": PrestacionForm,
            "referente_form": ReferenteForm,
            "anexo_form": AnexoForm,
        }

        for form_name, form_class in forms.items():
            data[form_name] = form_class(
                self.request.POST if self.request.POST else None,
                instance=getattr(
                    self.object, form_name.split("_form", maxsplit=1)[0], None
                ),
            )

        data["comedor"] = Comedor.objects.values(
            "id",
            "nombre",
            "referente__nombre",
            "referente__apellido",
            "referente__mail",
            "referente__celular",
            "referente__documento",
        ).get(pk=self.kwargs["comedor_pk"])
        data["espacio_cocina_form"] = EspacioCocinaForm(
            self.request.POST if self.request.POST else None,
            instance=getattr(self.object.espacio, "cocina", None),
        )
        data["espacio_prestacion_form"] = EspacioPrestacionForm(
            self.request.POST if self.request.POST else None,
            instance=getattr(self.object.espacio, "prestacion", None),
        )
        data["responsable"] = self.object.responsable

        return data

    def form_valid(self, form):
        context = self.get_context_data()
        forms = {
            "funcionamiento_form": context["funcionamiento_form"],
            "espacio_form": context["espacio_form"],
            "espacio_cocina_form": context["espacio_cocina_form"],
            "espacio_prestacion_form": context["espacio_prestacion_form"],
            "colaboradores_form": context["colaboradores_form"],
            "recursos_form": context["recursos_form"],
            "compras_form": context["compras_form"],
            "prestacion_form": context["prestacion_form"],
            "referente_form": context["referente_form"],
            "anexo_form": context["anexo_form"],
        }

        if all(form.is_valid() for form in forms.values()):
            self.object = RelevamientoService.populate_relevamiento(form, forms)

            return redirect(
                "relevamiento_detalle",
                comedor_pk=int(self.object.comedor.id),
                pk=int(self.object.id),
            )
        else:
            self.error_message(forms)
            return self.form_invalid(form)

    def error_message(self, forms):
        for form_name, form_instance in forms.items():
            if not form_instance.is_valid():
                messages.error(
                    self.request, f"Errores en {form_name}: {form_instance.errors}"
                )


class RelevamientoDeleteView(DeleteView):
    model = Relevamiento
    template_name = "relevamiento/relevamiento_confirm_delete.html"
    context_object_name = "relevamiento"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


class ObservacionCreateView(CreateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context.update(
            {
                "comedor": Comedor.objects.values("id", "nombre").get(
                    pk=self.kwargs["comedor_pk"]
                )
            }
        )

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = User.objects.get(pk=self.request.user.id)
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()

        self.object = form.save()

        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDetailView(DetailView):
    model = Observacion
    template_name = "observacion/observacion_detail.html"
    context_object_name = "observacion"

    def get_object(self, queryset=None) -> Model:
        return (
            Observacion.objects.prefetch_related("comedor")
            .values(
                "id",
                "fecha_visita",
                "observacion",
                "comedor__id",
                "comedor__nombre",
                "observador",
            )
            .get(pk=self.kwargs["pk"])
        )


class ObservacionUpdateView(UpdateView):
    model = Observacion
    form_class = ObservacionForm
    template_name = "observacion/observacion_form.html"
    context_object_name = "observacion"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        comedor = Comedor.objects.values("id", "nombre").get(
            pk=self.kwargs["comedor_pk"]
        )

        context.update({"comedor": comedor})

        return context

    def form_valid(self, form: BaseModelForm) -> HttpResponse:
        form.instance.comedor_id = Comedor.objects.get(pk=self.kwargs["comedor_pk"]).id
        usuario = User.objects.get(pk=self.request.user.id)
        form.instance.observador = f"{usuario.first_name} {usuario.last_name}"
        form.instance.fecha_visita = timezone.now()

        self.object = form.save()

        return redirect(
            "observacion_detalle",
            comedor_pk=int(self.kwargs["comedor_pk"]),
            pk=int(self.object.id),
        )


class ObservacionDeleteView(DeleteView):
    model = Observacion
    template_name = "observacion/observacion_confirm_delete.html"
    context_object_name = "observacion"

    def get_success_url(self):
        comedor = self.object.comedor

        return reverse_lazy("comedor_detalle", kwargs={"pk": comedor.id})


class RendicionCuentasFinalDetailView(DetailView):
    model = RendicionCuentasFinal
    context_object_name = "rendicion"
    template_name = "comedor/rendicion_cuentas_final_detail.html"

    def get_object(self, queryset=None) -> Model:
        comedor = get_object_or_404(
            Comedor.objects.only("id", "nombre"),  # Trae solo lo que vas a usar
            pk=self.kwargs["pk"],
        )
        rendicion, _ = RendicionCuentasFinal.objects.select_related(
            "comedor"
        ).get_or_create(comedor=comedor)

        return rendicion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rendicion = self.object

        context["documentos"] = (
            RendicionCuentasFinalService.get_documentos_rendicion_cuentas_final(
                rendicion
            )
        )

        context["historial"] = (
            HistorialService.get_historial_documentos_by_rendicion_cuentas_final(
                rendicion
            )
        )

        context["comedor_id"] = rendicion.comedor.id
        context["comedor_nombre"] = rendicion.comedor.nombre
        context["fisicamente_presentada"] = rendicion.fisicamente_presentada

        return context


@require_POST
def adjuntar_documento_rendicion_cuenta_final(request):
    doc_id = request.POST.get("documento_id")
    archivo = request.FILES.get("archivo")

    ok, _documento = RendicionCuentasFinalService.adjuntar_archivo_a_documento(
        doc_id, archivo
    )

    if not ok:
        messages.error(request, "No se seleccionó ningún archivo.")
    else:
        messages.success(request, "Archivo adjuntado correctamente.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def crear_documento_rendicion_cuentas_final(request, rendicion_id):
    rendicion = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    nombre = request.POST.get("nombre", "").strip()
    archivo = request.FILES.get("archivo")

    documento = rendicion.add_documento_personalizado(nombre)

    if archivo:
        HistorialService.registrar_historial(
            accion="Crear documento personalizado",
            instancia=documento,
        )

        RendicionCuentasFinalService.actualizar_documento_con_archivo(
            documento, archivo
        )

    return redirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def eliminar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

    documento.delete()
    messages.success(request, "Documento eliminado correctamente.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def validar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)
    documento.estado = EstadoDocumentoRendicionFinal.objects.get(nombre="Validado")
    documento.fecha_modificacion = timezone.now()
    documento.save()

    HistorialService.registrar_historial(
        accion="Validar documento",
        instancia=documento,
    )

    messages.success(request, "Documento validado correctamente.")

    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect(request.META.get("HTTP_REFERER", "/"))


class DocumentosRendicionCuentasFinalListView(ListView):
    model = DocumentoRendicionFinal
    template_name = "comedor/rendicion_cuentas_final_list.html"
    context_object_name = "documentos"

    def get_queryset(self):
        user = self.request.user
        query = self.request.GET.get("busqueda")

        qs = RendicionCuentasFinalService.filter_documentos_por_area(user, query)

        return qs


@require_POST
def subsanar_documento_rendicion_cuentas_final(request, documento_id):
    documento = get_object_or_404(DocumentoRendicionFinal, id=documento_id)

    documento.observaciones = request.POST.get("observacion", "")
    documento.estado = EstadoDocumentoRendicionFinal.objects.get(nombre="Subsanar")
    documento.fecha_modificacion = timezone.now()
    documento.save()

    HistorialService.registrar_historial(
        accion="Enviar a subsanar documento",
        instancia=documento,
    )

    messages.success(request, "Documento enviado a subsanar correctamente.")

    return redirect(request.META.get("HTTP_REFERER", "/"))


@require_POST
def switch_rendicion_final_fisicamente_presentada(request, rendicion_id):
    rendicion_final = get_object_or_404(RendicionCuentasFinal, id=rendicion_id)
    rendicion_final.fisicamente_presentada = not rendicion_final.fisicamente_presentada
    rendicion_final.save()

    messages.success(request, "Estado de revisión actualizado.")

    return redirect(request.META.get("HTTP_REFERER", "/"))
