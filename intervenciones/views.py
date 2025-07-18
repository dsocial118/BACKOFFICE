from django.http import JsonResponse
from django.core.cache import cache
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, DeleteView, TemplateView

from comedores.services.comedor_service import ComedorService
from intervenciones.models.intervenciones import (
    Intervencion,
    SubIntervencion,
    TipoIntervencion,
    TipoDestinatario,
)
from intervenciones.forms import IntervencionForm


@require_GET
def sub_estados_intervenciones_ajax(request):
    """Devolver sub estados disponibles para un tipo de intervención.

    Args:
        request (HttpRequest): Petición con el ``id`` del tipo.

    Returns:
        JsonResponse: Lista de subestados en formato Select2.
    """
    tipo_intervencion_id = request.GET.get("id")
    if tipo_intervencion_id:
        sub_estados = SubIntervencion.objects.filter(
            tipo_intervencion_id=tipo_intervencion_id
        )
    else:
        sub_estados = SubIntervencion.objects.none()

    data = [
        {"id": sub_estado.id, "text": sub_estado.nombre} for sub_estado in sub_estados
    ]
    return JsonResponse(data, safe=False)


class IntervencionDetailView(TemplateView):
    template_name = "intervencion_detail.html"
    model = Intervencion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        intervenciones, cantidad_intervenciones = (
            ComedorService.detalle_de_intervencion(self.kwargs)
        )
        intervenciones = Intervencion.objects.filter(comedor=comedor)
        fecha = self.request.GET.get("fecha")
        tipo_intervencion = self.request.GET.get("tipo_intervencion")
        destinatario = self.request.GET.get("destinatario")

        if fecha:
            intervenciones = intervenciones.filter(fecha__date=fecha)
        if tipo_intervencion:
            intervenciones = intervenciones.filter(
                tipo_intervencion_id=tipo_intervencion
            )
        if destinatario:
            intervenciones = intervenciones.filter(destinatario_id=destinatario)

        # Cache los tipos e intervenciones para evitar consultas repetidas
        context["tipos_intervencion"] = cache.get_or_set(
            "tipos_intervencion_all", list(TipoIntervencion.objects.all()), 300
        )
        context["destinatarios"] = cache.get_or_set(
            "destinatarios_all", list(TipoDestinatario.objects.all()), 300
        )
        context["intervenciones"] = intervenciones
        context["object"] = comedor
        context["cantidad_intervenciones"] = cantidad_intervenciones
        return context


class IntervencionCreateView(CreateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervencion_form.html"

    def form_valid(self, form):
        form.instance.comedor_id = self.kwargs["pk"]

        tipo_intervencion = form.cleaned_data.get("tipo_intervencion")
        if tipo_intervencion:
            subintervenciones = tipo_intervencion.subintervenciones.all()
            if subintervenciones.exists():
                subintervencion = form.cleaned_data.get("subintervencion")
                if not subintervencion:
                    form.add_error(
                        "subintervencion", "Debe seleccionar una subintervención."
                    )
                    return self.form_invalid(form)
            else:
                form.cleaned_data["subintervencion"] = None

        field_mapping = {
            "tipo_intervencion": TipoIntervencion,
            "subintervencion": SubIntervencion,
            "destinatario": "Destinatario",
            "fecha": "Fecha",
            "forma_contacto": "Forma de Contacto",
            "observaciones": "Descripción",
            "tiene_documentacion": "Documentación Adjunta",
        }

        for field, model in field_mapping.items():
            value = form.cleaned_data.get(field)
            if value is not None:
                if isinstance(model, type):
                    if isinstance(value, model):
                        setattr(form.instance, field, value)
                    else:
                        setattr(form.instance, field, model.objects.get(id=value))
                else:
                    setattr(form.instance, field, value)

        form.instance.save()
        return redirect(
            reverse("comedor_intervencion_ver", kwargs={"pk": self.kwargs["pk"]})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk"])
        context["object"] = comedor
        return context

    def get_success_url(self):
        return reverse("comedor_intervencion_ver", kwargs={"pk": self.object.pk})


class IntervencionUpdateView(UpdateView):
    model = Intervencion
    form_class = IntervencionForm
    template_name = "intervencion_form.html"

    def form_valid(self, form):
        pk = self.kwargs["pk2"]
        form.save()
        return redirect("comedor_intervencion_ver", pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = ComedorService.get_comedor(self.kwargs["pk2"])
        context["form"] = self.get_form()
        context["object"] = comedor
        return context


class IntervencionDeleteView(DeleteView):
    model = Intervencion
    template_name = "intervencion_confirm_delete.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Intervencion, id=self.kwargs["intervencion_id"])

    def get_success_url(self):
        return reverse(
            "comedor_intervencion_ver", kwargs={"pk": self.kwargs["comedor_id"]}
        )


def subir_archivo_intervencion(request, intervencion_id):
    """Guardar un archivo adjunto a la intervención.

    Args:
        request (HttpRequest): Petición que contiene el archivo.
        intervencion_id (int): Identificador de la intervención.

    Returns:
        JsonResponse: Resultado de la operación.
    """
    intervencion = get_object_or_404(Intervencion, id=intervencion_id)

    if request.method == "POST" and request.FILES.get("documentacion"):
        intervencion.documentacion = request.FILES["documentacion"]
        intervencion.tiene_documentacion = True
        intervencion.save()
        return JsonResponse(
            {"success": True, "message": "Archivo subido correctamente."}
        )

    return JsonResponse({"success": False, "message": "No se proporcionó un archivo."})


def eliminar_archivo_intervencion(request, intervencion_id):
    """Eliminar el archivo asociado a una intervención.

    Args:
        request (HttpRequest): Petición recibida.
        intervencion_id (int): Identificador de la intervención.

    Returns:
        HttpResponseRedirect: Redirección al detalle de la intervención.
    """
    intervencion = get_object_or_404(Intervencion, id=intervencion_id)

    if intervencion.documentacion:
        intervencion.documentacion.delete()
        intervencion.tiene_documentacion = False
        intervencion.save()
        messages.success(request, "El archivo fue eliminado correctamente.")
    else:
        messages.error(request, "No hay archivo para eliminar.")

    return redirect("intervencion_detalle", pk=intervencion.id)


class IntervencionDetailIndividualView(TemplateView):
    template_name = "intervencion_detail_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        intervencion = get_object_or_404(Intervencion, id=self.kwargs["pk"])
        context["intervencion"] = intervencion
        return context
