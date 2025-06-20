import os
import threading
import logging
import requests

from comedores.models import Comedor, Observacion, Referente


logger = logging.getLogger(__name__)
TIMEOUT = 360  # Segundos máximos de espera por respuesta


class AsyncSendComedorToGestionar(threading.Thread):
    """Hilo para enviar comedor a GESTIONAR asincronamente"""

    def __init__(self, comedor_id):
        super().__init__()
        self.comedor_id = comedor_id

    def run(self):
        comedor = Comedor.objects.get(id=self.comedor_id)

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
                    "lote": (comedor.lote if comedor.lote else ""),
                    "manzana": (comedor.manzana if comedor.manzana else ""),
                    "partido": comedor.partido if comedor.partido else "",
                    "barrio": comedor.barrio if comedor.barrio else "",
                    "piso": comedor.piso if comedor.piso else "",
                    "departamento": (
                        comedor.departamento if comedor.departamento else ""
                    ),
                    "codigo_postal": (
                        comedor.codigo_postal if comedor.codigo_postal else ""
                    ),
                    "Organizacion": (
                        comedor.organizacion.nombre if comedor.organizacion else ""
                    ),
                    "Referente": (
                        comedor.referente.documento
                        if comedor.referente and comedor.referente.documento
                        else ""
                    ),
                    "Imagen": (
                        f"{os.getenv('DOMINIO')}media/{comedor.foto_legajo}"
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
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response = response.json()
            logger.info(f"COMEDOR {comedor.id} sincronizado con GESTIONAR con exito")
        except Exception as e:
            logger.error(
                f"Error al sincronizar COMEDOR {comedor.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")


class AsyncRemoveComedorToGestionar(threading.Thread):
    """Hilo para eliminar comedor a GESTIONAR asincronamente"""

    def __init__(self, comedor_id):
        super().__init__()
        self.comedor_id = comedor_id

    def run(self):
        comedor = Comedor.objects.get(id=self.comedor_id)
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
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            logger.info(f"COMEDOR {comedor.id} sincronizado con exito")
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Error al sincronizar eliminacion de COMEDOR {comedor.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")


class AsyncSendReferenteToGestionar(threading.Thread):
    """Hilo para enviar referente a GESTIONAR asincronamente"""

    def __init__(self, referente_id):
        super().__init__()
        self.referente_id = referente_id

    def run(self):
        referente = Referente.objects.get(id=self.referente_id)

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
                    timeout=TIMEOUT,
                )
                response.raise_for_status()
                response = response.json()
                logger.info(
                    f"REFERENTE {referente.id} sincronizado con GESTIONAR con exito"
                )

        except Exception as e:
            logger.error(
                f"Error al sincronizar REFERENTE {referente.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")


class AsyncSendObservacionToGestionar(threading.Thread):
    """Hilo para enviar observacion a GESTIONAR asincronamente"""

    def __init__(self, observacion_id):
        super().__init__()
        self.observacion_id = observacion_id

    def run(self):
        observacion = Observacion.objects.get(id=self.observacion_id)

        data = {
            "Action": "Add",
            "Properties": {"Locale": "es-ES"},
            "Rows": [
                {
                    "Comedor_Id": observacion.comedor.id,
                    "OBSERVACION": observacion.observacion,
                    "Adjunto": "",
                    "Usr": "",
                    "FechaHora": observacion.fecha_visita.strftime("%d/%m/%Y %H:%M"),
                }
            ],
        }

        headers = {
            "applicationAccessKey": os.getenv("GESTIONAR_API_KEY"),
        }

        try:
            response = requests.post(
                os.getenv("GESTIONAR_API_CREAR_OBSERVACION"),
                json=data,
                headers=headers,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            response = response.json()
            logger.info(f"OBSERVACION {observacion.id} sincronizada con exito")
        except Exception as e:
            logger.error(
                f"Error al sincronizar OBSERVACION {observacion.id} con GESTIONAR: {e}"
            )
            logger.error(f"Con el body: {data}")
