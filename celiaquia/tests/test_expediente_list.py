import pytest
from django.urls import reverse
from django.contrib.auth.models import User, Group

from users.models import Profile
from core.models import Provincia
from celiaquia.models import Expediente, EstadoExpediente


@pytest.mark.django_db
def test_expediente_list_displays_id_and_provincia(client):
    grupo = Group.objects.create(name="ProvinciaCeliaquia")
    provincia = Provincia.objects.create(nombre="Buenos Aires")
    user = User.objects.create_user(username="prov", password="pass")
    Profile.objects.create(user=user, es_usuario_provincial=True, provincia=provincia)
    user.groups.add(grupo)
    estado = EstadoExpediente.objects.create(nombre="CREADO")
    expediente = Expediente.objects.create(usuario_provincia=user, estado=estado)

    client.force_login(user)
    response = client.get(reverse("expediente_list"))

    content = response.content.decode()
    assert str(expediente.pk) in content
    assert provincia.nombre in content
