from django.urls import path

from relevamientos.views.api_views import (
    RelevamientoApiView,
)

urlpatterns = [
    path(
        "api/relevamiento",
        RelevamientoApiView.as_view(),
        name="api_relevamiento",
    ),
]
