from unittest import mock

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_crear(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la creación de un nuevo relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    # Mock del servicio de relevamiento para evitar llamadas reales durante el test
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 999
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_editar(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba la edición de un relevamiento vía AJAX.
    Verifica que:
    1. Se invoque al servicio correcto
    2. Se retorne la URL de redirección adecuada
    3. El código de estado sea 200
    """
    relevamiento_mock = mock.Mock()
    relevamiento_mock.pk = 1000
    relevamiento_mock.comedor = mock.Mock()
    relevamiento_mock.comedor.pk = comedor_fixture.pk

    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.update_territorial",
        mock.Mock(return_value=relevamiento_mock),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial_editar": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 200
    json_response = response.json()
    assert "url" in json_response
    # Verificar que la URL tenga el formato correcto con los IDs esperados
    expected_url = (
        f"/comedores/{comedor_fixture.pk}/relevamiento/{relevamiento_mock.pk}"
    )
    assert json_response["url"] == expected_url


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_accion_invalida(
    client_logged_fixture, comedor_fixture
):
    """
    Prueba que una acción inválida retorne un error.
    """
    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {"accion_invalida": "1"}
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 400
    json_response = response.json()
    assert "error" in json_response
    assert "Acción no reconocida" in json_response["error"]


@pytest.mark.django_db
def test_relevamiento_create_edit_ajax_error(
    client_logged_fixture, comedor_fixture, monkeypatch
):
    """
    Prueba el manejo de errores durante la creación/edición.
    """
    monkeypatch.setattr(
        "relevamientos.service.RelevamientoService.create_pendiente",
        mock.Mock(side_effect=Exception("Error inesperado")),
    )

    url = reverse("relevamiento_create_edit_ajax", kwargs={"pk": comedor_fixture.pk})
    data = {
        "territorial": "1",
    }
    response = client_logged_fixture.post(
        url, data, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
    )

    assert response.status_code == 500
    json_response = response.json()
    assert "error" in json_response
    assert "Error inesperado" in json_response["error"]
