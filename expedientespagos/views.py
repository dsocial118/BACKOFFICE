from django.http import HttpResponseRedirect, Http404
from django.contrib import messages
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy, reverse
from expedientespagos.models import ExpedientePago
from expedientespagos.forms import ExpedientePagoForm
from expedientespagos.services import ExpedientesPagosService
from comedores.models import Comedor


class ExpedientesPagosListView(ListView):
    model = ExpedientePago
    template_name = "expedientespagos_list.html"
    context_object_name = "expedientespagos"
    paginate_by = 10

    def get_queryset(self):
        """Retorna expedientes ordenados para evitar warning de paginación"""
        return ExpedientePago.objects.order_by("-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["expedientes_pagos"] = (
            ExpedientesPagosService.obtener_expedientes_pagos(comedor_id)
        )
        context["comedorid"] = comedor_id

        # Configuración para el componente data_table
        context["table_headers"] = [
            {"title": "Número de Expediente"},
            {"title": "Resolución de Pago"},
            {"title": "Monto"},
            {"title": "Anexo"},
            {"title": "Número de Orden de Pago"},
            {"title": "Fecha de pago al banco"},
            {"title": "Fecha de acreditación"},
            {"title": "Observaciones"},
            {"title": "Fecha de creación"},
        ]

        context["table_fields"] = [
            {"name": "expediente_pago"},
            {"name": "resolucion_pago"},
            {"name": "monto"},
            {"name": "anexo"},
            {"name": "numero_orden_pago"},
            {"name": "fecha_pago_al_banco"},
            {"name": "fecha_acreditacion"},
            {"name": "observaciones"},
            {"name": "fecha_creacion"},
        ]

        context["table_actions"] = [
            {"label": "Ver", "url_name": "expedientespagos_detail", "type": "info"}
        ]

        return context


class ExpedientesPagosDetailView(DetailView):
    model = ExpedientePago
    template_name = "expedientespagos_detail.html"
    context_object_name = "expediente_pago"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["expediente"] = ExpedientesPagosService.obtener_expediente_pago(
            self.kwargs.get("pk")
        )
        return context


class ExpedientesPagosCreateView(CreateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.kwargs.get("pk")}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor_id = self.kwargs.get("pk")
        context["comedorid"] = comedor_id
        context["form"] = ExpedientePagoForm()
        context["es_area_legales"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Area Legales").exists()
        )
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        # URL de cancelación para el componente form_buttons
        from django.urls import reverse

        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": comedor_id}
        )
        return context

    def post(self, request, *args, **kwargs):
        comedor_id = self.kwargs.get("pk")
        form = ExpedientePagoForm(request.POST)
        comedor = Comedor.objects.get(pk=comedor_id)
        if form.is_valid():
            # Crear el objeto y asignarlo a self.object
            self.object = ExpedientesPagosService.crear_expediente_pago(
                comedor, form.cleaned_data
            )
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosUpdateView(UpdateView):
    model = ExpedientePago
    template_name = "expedientespagos_form.html"
    form_class = ExpedientePagoForm

    def get_success_url(self):
        return reverse_lazy(
            "expedientespagos_list", kwargs={"pk": self.object.comedor.id}
        )

    def form_valid(self, form):
        # Mantén el mismo comedor que tenía originalmente
        form.instance.comedor = self.get_object().comedor
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expediente = self.get_object()
        context["comedorid"] = expediente.comedor.id
        context["es_area_legales"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Area Legales").exists()
        )
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        # URL de cancelación para el componente form_buttons
        from django.urls import reverse

        context["expedientes_list_url"] = reverse(
            "expedientespagos_list", kwargs={"pk": expediente.comedor.id}
        )
        return context

    def post(self, request, *args, **kwargs):
        # Configurar self.object antes de llamar a form_valid
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class ExpedientesPagosDeleteView(DeleteView):
    model = ExpedientePago
    template_name = "expedientespagos_confirm_delete.html"

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except ExpedientePago.DoesNotExist as exc:
            raise Http404("El expediente de pago no existe.") from exc

    def get_success_url(self):
        return reverse("lista_comedores_acompanamiento")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Expediente eliminado correctamente.")
        return HttpResponseRedirect(self.get_success_url())
