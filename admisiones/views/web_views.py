import os
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from admisiones.forms.admisiones_forms import (
    AdmisionForm,
    CaratularForm,
    LegalesRectificarForm,
    ProyectoConvenioForm,
    ResoForm,
    LegalesNumIFForm,
)
from admisiones.models.admisiones import (
    Admision,
    ArchivoAdmision,
    ArchivoAdmision,
    InformeTecnicoPDF,
    FormularioProyectoDeConvenio,
    FormularioRESO,
)
from admisiones.services.admisiones_service import AdmisionService
from django.views.generic.edit import FormMixin

from django.urls import reverse
from django.http import HttpResponseRedirect


@csrf_exempt
def subir_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "POST" and request.FILES.get("archivo"):
        archivo_admision, created = AdmisionService.handle_file_upload(
            admision_id, documentacion_id, request.FILES["archivo"]
        )
        return JsonResponse({"success": True, "estado": archivo_admision.estado})
    return JsonResponse(
        {"success": False, "error": "No se recibió un archivo"}, status=400
    )


def eliminar_archivo_admision(request, admision_id, documentacion_id):
    if request.method == "DELETE":
        archivo = get_object_or_404(
            ArchivoAdmision, admision_id=admision_id, documentacion_id=documentacion_id
        )
        AdmisionService.delete_admision_file(archivo)
        return JsonResponse({"success": True, "nombre": archivo.documentacion.nombre})
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


def actualizar_estado_archivo(request):
    resultado = AdmisionService.actualizar_estado_ajax(request)

    if resultado.get("success"):
        return JsonResponse(
            {
                "success": True,
                "nuevo_estado": resultado.get("nuevo_estado"),
                "grupo_usuario": resultado.get("grupo_usuario"),
                "mostrar_select": resultado.get("mostrar_select", False),
                "opciones": resultado.get("opciones", []),
            }
        )
    else:
        return JsonResponse(
            {
                "success": False,
                "error": resultado.get("error", "Error desconocido"),
            },
            status=400,
        )


class AdmisionesTecnicosListView(ListView):
    model = Admision
    template_name = "admisiones_tecnicos_list.html"
    context_object_name = "comedores"

    def get_queryset(self):
        return AdmisionService.get_comedores_with_admision(self.request.user)


class AdmisionesTecnicosCreateView(CreateView):
    model = Admision
    template_name = "admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_create_context(self.kwargs["pk"]))
        return context

    def post(self, request, *args, **kwargs):
        tipo_convenio_id = request.POST.get("tipo_convenio")
        if tipo_convenio_id:
            admision = AdmisionService.create_admision(
                self.kwargs["pk"], tipo_convenio_id
            )
            return redirect("admisiones_tecnicos_editar", pk=admision.pk)
        return self.get(request, *args, **kwargs)


class AdmisionesTecnicosUpdateView(UpdateView):
    model = Admision
    template_name = "admisiones_tecnicos_form.html"
    form_class = AdmisionForm
    context_object_name = "admision"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.get_admision_update_context(self.get_object()))
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()

        if "mandarLegales" in request.POST:
            if AdmisionService.marcar_como_enviado_a_legales(admision, request.user):
                messages.success(
                    request, "La admisión fue enviada a legales correctamente."
                )
            else:
                messages.info(
                    request, "La admisión ya estaba marcada como enviada a legales."
                )
            return redirect(self.request.path_info)

        if "btnRectificarDocumentacion" in request.POST:
            if AdmisionService.marcar_como_documentacion_rectificada(
                admision, request.user
            ):
                messages.success(request, "Se rectificó la documentación.")
            else:
                messages.error(request, "Error al querer realizar la rectificación.")
            return redirect(self.request.path_info)

        if "btnCaratulacion" in request.POST:
            form = CaratularForm(request.POST, instance=admision)
            if form.is_valid():
                form.save()
                messages.success(
                    request, "Caratulación del expediente guardado correctamente."
                )
            else:
                messages.error(request, "Error al guardar la caratulación.")
            return redirect(self.request.path_info)

        if "tipo_convenio" in request.POST:
            if AdmisionService.update_convenio(
                admision, request.POST.get("tipo_convenio")
            ):
                messages.success(request, "Tipo de convenio actualizado correctamente.")
            return redirect(self.request.path_info)

        return super().post(request, *args, **kwargs)


class InformeTecnicosCreateView(CreateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_form_class_por_tipo(tipo)

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def form_valid(self, form):
        tipo = self.kwargs.get("tipo", "base")
        admision_id = self.kwargs.get("admision_id")
        AdmisionService.preparar_informe_para_creacion(form.instance, admision_id)
        return super().form_valid(form)

    def get_success_url(self):
        admision_id = self.object.admision.id
        return reverse("admisiones_tecnicos_editar", args=[admision_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admision_id = self.kwargs.get("admision_id")
        context["tipo"] = self.kwargs.get("tipo", "base")
        context["admision"] = AdmisionService.get_admision(admision_id)
        return context


class InformeTecnicosUpdateView(UpdateView):
    template_name = "informe_tecnico_form.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def get_form_class(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_form_class_por_tipo(tipo)

    def form_valid(self, form):
        AdmisionService.verificar_estado_para_revision(form.instance)
        return super().form_valid(form)

    def get_success_url(self):
        admision_id = self.object.admision.id
        return reverse("admisiones_tecnicos_editar", args=[admision_id])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        informe = self.object
        context.update(
            {
                "tipo": tipo,
                "admision": informe.admision,
                "comedor": informe.admision.comedor,
                "campos": AdmisionService.get_campos_visibles_informe(informe),
            }
        )
        return context


class InformeTecnicoDetailView(DetailView):
    template_name = "informe_tecnico_detalle.html"
    context_object_name = "informe_tecnico"

    def get_queryset(self):
        tipo = self.kwargs.get("tipo", "base")
        return AdmisionService.get_queryset_informe_por_tipo(tipo)

    def post(self, request, *args, **kwargs):
        tipo = self.kwargs.get("tipo", "base")
        informe = AdmisionService.get_informe_por_tipo_y_pk(tipo, kwargs["pk"])

        nuevo_estado = request.POST.get("estado")
        if nuevo_estado in ["A subsanar", "Validado"]:
            AdmisionService.actualizar_estado_informe(informe, nuevo_estado, tipo)

        admision_id = informe.admision.id
        return HttpResponseRedirect(
            reverse("admisiones_tecnicos_editar", args=[admision_id])
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tipo = self.kwargs.get("tipo", "base")
        informe = self.object

        context["tipo"] = tipo
        context["admision"] = informe.admision
        context["campos"] = AdmisionService.get_campos_visibles_informe(informe)
        context["pdf"] = InformeTecnicoPDF.objects.filter(
            admision=informe.admision, tipo=tipo, informe_id=informe.id
        ).first()
        return context


class AdmisionesLegalesListView(ListView):
    model = Admision
    template_name = "admisiones_legales_list.html"
    context_object_name = "admisiones"

    def get_queryset(self):
        return Admision.objects.filter(enviado_legales=True)


class AdmisionesLegalesDetailView(FormMixin, DetailView):
    model = Admision
    template_name = "admisiones_legales_detalle.html"
    context_object_name = "admision"
    form_class = LegalesRectificarForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.legales_detalle_context(self.get_object()))
        return context

    def get_success_url(self):
        return reverse("admisiones_legales_ver", kwargs={"pk": self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(AdmisionService.legales_detalle_context(self.get_object()))
        if "form" not in context:
            context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        admision = self.get_object()

        if "btnLegalesNumIF" in request.POST:
            return AdmisionService.guardar_legales_num_if(request, admision)

        if "ValidacionJuridicos" in request.POST:
            return AdmisionService.validar_juridicos(request, admision)

        if "btnRESO" in request.POST:
            return AdmisionService.guardar_formulario_reso(request, admision)

        if "btnProyectoConvenio" in request.POST:
            return AdmisionService.guardar_formulario_proyecto_convenio(
                request, admision
            )

        if "btnObservaciones" in request.POST:
            return AdmisionService.enviar_a_rectificar(request, admision)

        if "btnDocumentoExpediente" in request.POST:
            return AdmisionService.guardar_documento_expediente(request, admision)
