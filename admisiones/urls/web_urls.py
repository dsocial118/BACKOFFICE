from django.urls import path
from core.decorators import group_required
from admisiones.views.web_views import (
    subir_archivo_admision,
    eliminar_archivo_admision,
    actualizar_estado_archivo,
    AdmisionesTecnicosListView,
    AdmisionesTecnicosCreateView,
    AdmisionesTecnicosUpdateView,
    InformeTecnicosCreateView,
    InformeTecnicosUpdateView,
    InformeTecnicoDetailView,
    InformeTecnicoComplementarioDetailView,
    AdmisionesLegalesListView,
    AdmisionesLegalesDetailView,
    AnexoCreateView,
    AnexoUpdateView,
)
from intervenciones.views import sub_estados_intervenciones_ajax

urlpatterns = [
    path(
        "comedores/admisiones/tecnicos/listar",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            AdmisionesTecnicosListView.as_view()
        ),
        name="admisiones_tecnicos_listar",
    ),
    path(
        "comedores/admisiones/tecnicos/crear/<int:pk>",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            AdmisionesTecnicosCreateView.as_view()
        ),
        name="admisiones_tecnicos_crear",
    ),
    path(
        "comedores/admisiones/tecnicos/editar/<int:pk>",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            AdmisionesTecnicosUpdateView.as_view()
        ),
        name="admisiones_tecnicos_editar",
    ),
    path(
        "admision/<int:admision_id>/documentacion/<int:documentacion_id>/subir/",
        subir_archivo_admision,
        name="subir_archivo_admision",
    ),
    path(
        "admision/<int:admision_id>/documentacion/<int:documentacion_id>/eliminar/",
        eliminar_archivo_admision,
        name="eliminar_archivo_admision",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:admision_id>/crear/",
        group_required(["Comedores", "Tecnico Comedor"])(
            InformeTecnicosCreateView.as_view()
        ),
        name="informe_tecnico_crear",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:pk>/editar/",
        group_required(["Comedores", "Tecnico Comedor"])(
            InformeTecnicosUpdateView.as_view()
        ),
        name="informe_tecnico_editar",
    ),
    path(
        "comedores/admision/informe_tecnico/<str:tipo>/<int:pk>/ver/",
        group_required(["Comedores", "Tecnico Comedor"])(
            InformeTecnicoDetailView.as_view()
        ),
        name="informe_tecnico_ver",
    ),
    path(
        "comedores/admision/informe_complementario/<str:tipo>/<int:pk>/ver/",
        group_required(["Comedores", "Tecnico Comedor", "Abogado Dupla"])(
            InformeTecnicoComplementarioDetailView.as_view()
        ),
        name="informe_complementario_ver",
    ),
    path(
        "comedores/admision/anexo/<int:admision_id>/crear/",
        group_required(["Comedores", "Tecnico Comedor"])(AnexoCreateView.as_view()),
        name="anexo_crear",
    ),
    path(
        "comedores/admision/anexo/<int:admision_id>/editar/",
        group_required(["Comedores", "Tecnico Comedor"])(AnexoUpdateView.as_view()),
        name="anexo_editar",
    ),
    path(
        "ajax/actualizar-estado/",
        actualizar_estado_archivo,
        name="actualizar_estado_archivo",
    ),
    # Legales
    path(
        "comedores/admisiones/legales/listar",
        group_required(["Area Legales"])(AdmisionesLegalesListView.as_view()),
        name="admisiones_legales_listar",
    ),
    path(
        "comedores/admisiones/legales/ver/<int:pk>",
        group_required(["Area Legales"])(AdmisionesLegalesDetailView.as_view()),
        name="admisiones_legales_ver",
    ),
]
