import os
import re
from typing import Union

from django.db.models import Q
import requests

from comedores.models.relevamiento import Relevamiento
from comedores.forms.comedor_form import ImagenComedorForm
from comedores.models.comedor import Comedor, Referente, ValorComida
from configuraciones.models import Municipio, Provincia
from configuraciones.models import Localidad


class ComedorService:
    @staticmethod
    def get_comedores_filtrados(query: Union[str, None] = None):
        queryset = Comedor.objects.prefetch_related("provincia", "referente").values(
            "id",
            "nombre",
            "tipocomedor__nombre",
            "provincia__nombre",
            "municipio__nombre",
            "localidad__nombre",
            "barrio",
            "partido",
            "calle",
            "numero",
            "referente__nombre",
            "referente__apellido",
            "referente__celular",
        )
        if query:
            queryset = queryset.filter(
                Q(nombre__icontains=query)
                | Q(tipocomedor__nombre__icontains=query)
                | Q(provincia__nombre__icontains=query)
                | Q(municipio__nombre__icontains=query)
                | Q(localidad__nombre__icontains=query)
                | Q(barrio__icontains=query)
                | Q(calle__icontains=query)
            )
        return queryset

    @staticmethod
    def get_comedor_detail_object(comedor_id: int):
        return (
            Comedor.objects.select_related("provincia", "referente")
            .values(
                "id",
                "foto_legajo",
                "nombre",
                "comienzo",
                "organizacion__nombre",
                "programa__nombre",
                "provincia__nombre",
                "municipio__nombre",
                "localidad__nombre",
                "tipocomedor__nombre",
                "partido",
                "barrio",
                "calle",
                "numero",
                "piso",
                "departamento",
                "manzana",
                "lote",
                "longitud",
                "latitud",
                "entre_calle_1",
                "entre_calle_2",
                "codigo_postal",
                "referente__nombre",
                "referente__apellido",
                "referente__mail",
                "referente__celular",
                "referente__documento",
            )
            .get(pk=comedor_id)
        )

    @staticmethod
    def get_ubicaciones_ids(data):
        if "provincia" in data:
            provincia_obj = Provincia.objects.filter(
                nombre__iexact=data["provincia"]
            ).first()
            data["provincia"] = provincia_obj.id if provincia_obj else ""

        if "municipio" in data:
            municipio_obj = Municipio.objects.filter(
                nombre__iexact=data["municipio"]
            ).first()
            data["municipio"] = municipio_obj.id if municipio_obj else ""

        if "localidad" in data:
            localidad_obj = Localidad.objects.filter(
                nombre__iexact=data["localidad"]
            ).first()
            data["localidad"] = localidad_obj.id if localidad_obj else ""

        return data

    @staticmethod
    def create_or_update_referente(data, referente_instance=None):
        referente_data = data.get("referente", {})

        if "celular" in referente_data:
            referente_data["celular"] = referente_data["celular"].replace("-", "")
            if referente_data["celular"] == "":
                referente_data["celular"] = None
        if "documento" in referente_data:
            referente_data["documento"] = referente_data["documento"].replace(".", "")

        if referente_instance is None:  # Crear referente
            referente_instance = Referente.objects.create(**referente_data)
        else:  # Actualizar referente
            for field, value in referente_data.items():
                setattr(referente_instance, field, value)
            referente_instance.save()

        return referente_instance

    @staticmethod
    def create_imagenes(imagen, comedor_pk):
        imagen_comedor = ImagenComedorForm(
            {"comedor": comedor_pk},
            {"imagen": imagen},
        )
        if imagen_comedor.is_valid():
            return imagen_comedor.save()
        else:
            return imagen_comedor.errors

    @staticmethod
    def send_to_gestionar(comedor: Comedor):
        data = {
            "Action": "Add",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "ComedorID": comedor.id,
                    "ID_Sisoc": comedor.id,
                    "nombre": comedor.nombre,
                    "comienzo": (
                        f"01/01/{comedor.comienzo}"
                        if comedor.comienzo
                        else "01/01/1900"
                    ),
                    "TipoComedor": (
                        comedor.tipocomedor.nombre if comedor.tipocomedor else ""
                    ),
                    "calle": comedor.calle if comedor.calle else "",
                    "numero": comedor.numero if comedor.numero else "",
                    "entre_calle_1": (
                        comedor.entre_calle_1 if comedor.entre_calle_1 else ""
                    ),
                    "entre_calle_2": (
                        comedor.entre_calle_2 if comedor.entre_calle_2 else ""
                    ),
                    "provincia": (
                        comedor.provincia.nombre if comedor.provincia else ""
                    ),
                    "municipio": (
                        comedor.municipio.nombre if comedor.municipio else ""
                    ),
                    "localidad": (
                        comedor.localidad.nombre if comedor.localidad else ""
                    ),
                    "partido": comedor.partido if comedor.partido else "",
                    "barrio": comedor.barrio if comedor.barrio else "",
                    "codigo_postal": (
                        comedor.codigo_postal if comedor.codigo_postal else ""
                    ),
                    "Referente": (
                        comedor.referente.documento
                        if comedor.referente and comedor.referente.documento
                        else ""
                    ),
                    "Imagen": (
                        f"{os.getenv('DOMINIO')}/media/{comedor.foto_legajo}"
                        if comedor.foto_legajo
                        else ""
                    ),
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_COMEDOR"),
                json=data,
                headers=headers,
            )
            response.raise_for_status()
            response = response.json()

            gestionar_uid = response["Rows"][0]["ComedorID"]
            if comedor.gestionar_uid != gestionar_uid:
                comedor.gestionar_uid = gestionar_uid
                comedor.save()
        except requests.exceptions.RequestException as e:
            print("!!! Error al sincronizar creacion de COMEDOR con GESTIONAR:")
            print(e)
            print("!!! Con la data:")
            print(data)

    @staticmethod
    def send_referente_to_gestionar(referente: Referente):
        data = {
            "Action": "Add",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "documento": referente.documento,
                    "nombre": referente.nombre,
                    "apellido": referente.apellido,
                    "mail": referente.mail,
                    "celular": referente.celular,
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            if referente.documento is not None:
                response = requests.post(
                    os.getenv("GESTIONAR_API_CREAR_REFERENTE"),
                    json=data,
                    headers=headers,
                )
                response.raise_for_status()
                response = response.json()

        except requests.exceptions.RequestException as e:
            print("!!! Error al sincronizar REFERENTE con GESTIONAR:")
            print(e)
            print("!!! Con la data:")
            print(data)

    @staticmethod
    def remove_to_gestionar(comedor: Comedor):
        data = {
            "Action": "Delete",
            "Properties": {"Locale": "es-ES"},
            "Rows": [{"ComedorID": f"{comedor.id}"}],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_BORRAR_COMEDOR"),
                json=data,
                headers=headers,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print("!!! Error al sincronizar eliminacion de COMEDOR con GESTIONAR:")
            print(e)
            print("!!! Con la data:")
            print(data)

    @staticmethod
    def get_presupuestos(comedor_id: int):
        beneficiarios = Relevamiento.objects.filter(comedor=comedor_id).first()

        # Inicializamos contadores
        count = {
            "desayuno": 0,
            "almuerzo": 0,
            "merienda": 0,
            "cena": 0,
        }

        if beneficiarios and beneficiarios.prestacion:
            dias = [
                "lunes",
                "martes",
                "miercoles",
                "jueves",
                "viernes",
                "sabado",
                "domingo",
            ]
            tipos = ["desayuno", "almuerzo", "merienda", "cena"]

            for tipo in tipos:
                count[tipo] = sum(
                    getattr(beneficiarios.prestacion, f"{dia}_{tipo}_actual", 0) or 0
                    for dia in dias
                )

        count_beneficiarios = sum(count.values())

        # Cálculo de valores
        valores_comida = ValorComida.objects.filter(tipo__in=count.keys()).values(
            "tipo", "valor"
        )
        valor_map = {item["tipo"].lower(): item["valor"] for item in valores_comida}

        valor_cena = count["cena"] * valor_map.get("cena", 0)
        valor_desayuno = count["desayuno"] * valor_map.get("desayuno", 0)
        valor_almuerzo = count["almuerzo"] * valor_map.get("almuerzo", 0)
        valor_merienda = count["merienda"] * valor_map.get("merienda", 0)

        return (
            count_beneficiarios,
            valor_cena,
            valor_desayuno,
            valor_almuerzo,
            valor_merienda,
        )
