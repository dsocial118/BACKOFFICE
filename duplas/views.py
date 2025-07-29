from django.contrib import messages
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy

from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from duplas.models import Dupla
from duplas.forms import DuplaForm
from comedores.services.comedor_service import ComedorService


class DuplaListView(ListView):
    model = Dupla
    template_name = "dupla_list.html"
    context_object_name = "duplas"
    paginate_by = 10

    def get_queryset(self):
        queryset = (
            Dupla.objects.select_related("abogado")
            .prefetch_related("tecnico")
            .order_by("-fecha", "nombre")
        )
        
        # Agregar búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(nombre__icontains=search)
            
        return queryset


class DuplaCreateView(CreateView):
    model = Dupla
    template_name = "dupla_form.html"
    form_class = DuplaForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            try:
                self.object = self.form_valid(form)
                messages.success(request, "Dupla creada correctamente.")
                return HttpResponseRedirect(self.get_success_url())
            except ValidationError as e:
                messages.error(request, str(e))
                return self.form_invalid(form)
        else:
            messages.error(request, "Error al crear la Dupla.")
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaUpdateView(UpdateView):
    model = Dupla
    template_name = "dupla_form.html"
    form_class = DuplaForm
    success_url = reverse_lazy("dupla_list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.filtrar_campos_tecnico_abogado()
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        return context

    def get_success_url(self):
        return reverse("dupla_list")


class DuplaDetailView(DetailView):
    model = Dupla
    template_name = "dupla_detail.html"
    context_object_name = "dupla"

    def get_queryset(self):
        """Optimiza las queries para el detalle de dupla"""
        return Dupla.objects.select_related("abogado").prefetch_related("tecnico")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Agregar breadcrumb_items
        context['breadcrumb_items'] = [
            {'url': reverse('dupla_list'), 'text': 'Duplas'}
        ]
        
        return context


class DuplaDeleteView(DeleteView):
    model = Dupla
    template_name = "dupla_confirm_delete.html"
    success_url = reverse_lazy("dupla_list")

    def get_success_url(self):
        return reverse("dupla_list")

    def post(self, request, *args, **kwargs):
        comedor = ComedorService.get_comedor_by_dupla(kwargs["pk"])
        if comedor:
            messages.error(
                request,
                "No se puede eliminar la dupla porque está asignada al comedor "
                + str(comedor.nombre),
            )
            return HttpResponseRedirect(self.get_success_url())
        self.object = self.get_object()
        self.object.delete()
        messages.success(request, "Dupla eliminada correctamente.")
        return HttpResponseRedirect(self.get_success_url())
