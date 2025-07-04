from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.views.decorators.http import require_POST
from django.db.models import Q
from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    DocumentosExpediente,
)
from acompanamientos.acompanamiento_service import AcompanamientoService
from acompanamientos.models.hitos import Hitos
from comedores.models import Comedor


@require_POST
def restaurar_hito(request, comedor_id):
    campo = request.POST.get("campo")
    hito = get_object_or_404(Hitos, comedor_id=comedor_id)

    # Verifica si el campo existe en el modelo
    if hasattr(hito, campo):
        setattr(hito, campo, False)  # Cambia el valor del campo a False (0)
        hito.save()
        messages.success(
            request, f"El campo '{campo}' ha sido restaurado correctamente."
        )
    else:
        messages.error(request, f"El campo '{campo}' no existe en el modelo Hitos.")

    # Redirige a la página anterior
    return redirect(request.META.get("HTTP_REFERER", "/"))


# TODO: Sincronizar con la tarea de Pablo
class AcompanamientoDetailView(DetailView):
    model = Comedor
    template_name = "acompañamiento_detail.html"
    context_object_name = "comedor"
    pk_url_kwarg = "comedor_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comedor = self.object
        context["hitos"] = AcompanamientoService.obtener_hitos(comedor)
        context["es_tecnico_comedor"] = (
            self.request.user.is_superuser
            or self.request.user.groups.filter(name="Tecnico Comedor").exists()
        )
        admision = (
            Admision.objects.filter(comedor=comedor)
            .exclude(num_if__isnull=True)
            .exclude(num_if="")
            .order_by("-id")
            .first()
        )
        context["admision"] = admision

        info_relevante = None
        resolucion = None
        doc_resolucion = None

        if admision:
            info_relevante = (
                InformeTecnico.objects.filter(admision__comedor=comedor)
                .order_by("-id")
                .first()
            )
            doc_resolucion = (
                DocumentosExpediente.objects.filter(
                    admision__comedor=comedor, tipo="Resolución"
                )
                .order_by("-creado")
                .first()
            )
        if doc_resolucion:
            resolucion = doc_resolucion.value or doc_resolucion.nombre

        # Asignar valores al contexto
        context["info_relevante"] = info_relevante
        context["numero_if"] = admision.num_if if admision else None
        context["numero_resolucion"] = resolucion

        # Prestaciones
        if info_relevante:
            context["prestaciones_dias"] = [
                {"tipo": "Desayuno", "cantidad": info_relevante.prestaciones_desayuno},
                {"tipo": "Almuerzo", "cantidad": info_relevante.prestaciones_almuerzo},
                {"tipo": "Merienda", "cantidad": info_relevante.prestaciones_merienda},
                {"tipo": "Cena", "cantidad": info_relevante.prestaciones_cena},
            ]
        else:
            context["prestaciones_dias"] = []

        return context


class ComedoresAcompanamientoListView(ListView):
    model = Comedor
    template_name = "lista_comedores.html"
    context_object_name = "comedores"
    paginate_by = 10  # Cantidad de resultados por página

    def get_queryset(self):
        user = self.request.user
        busqueda = self.request.GET.get("busqueda", "").strip().lower()

        # Filtramos las admisiones con estado=2 (Finalizada)
        admisiones = Admision.objects.filter(estado=2, enviado_acompaniamiento=True)

        # Si no es superusuario, filtramos por dupla asignada

        if (
            not user.is_superuser
            and not user.groups.filter(name="Area Legales").exists()
        ):
            admisiones = admisiones.filter(
                Q(comedor__dupla__abogado=user) | Q(comedor__dupla__tecnico=user)
            )

        # Obtenemos los IDs de los comedores que tienen admisiones finalizadas
        comedor_ids = admisiones.values_list("comedor_id", flat=True).distinct()

        # Filtramos los comedores
        queryset = Comedor.objects.filter(id__in=comedor_ids).select_related(
            "referente", "tipocomedor", "provincia"
        )

        # Aplicamos búsqueda global
        if busqueda:
            queryset = queryset.filter(
                Q(nombre__icontains=busqueda)
                | Q(provincia__nombre__icontains=busqueda)
                | Q(tipocomedor__nombre__icontains=busqueda)
                | Q(calle__icontains=busqueda)
                | Q(numero__icontains=busqueda)
                | Q(referente__nombre__icontains=busqueda)
                | Q(referente__apellido__icontains=busqueda)
                | Q(referente__celular__icontains=busqueda)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("busqueda", "")
        return context
