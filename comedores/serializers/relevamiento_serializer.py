from rest_framework import serializers

from comedores.models.relevamiento import Relevamiento

from comedores.services.relevamiento_service import RelevamientoService
from comedores.utils import format_fecha_django


class RelevamientoSerializer(serializers.ModelSerializer):

    def clean(self):
        if "fecha_visita" in self.initial_data:
            self.initial_data["fecha_visita"] = format_fecha_django(
                self.initial_data["fecha_visita"]
            )

        if "territorial" in self.initial_data:
            territorial_data = self.initial_data["territorial"]
            self.initial_data["territorial_nombre"] = territorial_data["nombre"]
            self.initial_data["territorial_uid"] = territorial_data["gestionar_uid"]

        if "funcionamiento" in self.initial_data:
            funcionamiento_instance = (
                self.instance.funcionamiento
                if self.instance and self.instance.funcionamiento
                else None
            )
            self.initial_data["funcionamiento"] = (
                RelevamientoService.create_or_update_funcionamiento(
                    self.initial_data["funcionamiento"], funcionamiento_instance
                ).id
            )

        if "espacio" in self.initial_data:
            espacio_instance = (
                self.instance.espacio
                if self.instance and self.instance.espacio
                else None
            )
            self.initial_data["espacio"] = RelevamientoService.create_or_update_espacio(
                self.initial_data["espacio"], espacio_instance
            ).id

        if "colaboradores" in self.initial_data:
            colaboradores_instance = (
                self.instance.colaboradores
                if self.instance and self.instance.colaboradores
                else None
            )
            self.initial_data["colaboradores"] = (
                RelevamientoService.create_or_update_colaboradores(
                    self.initial_data["colaboradores"], colaboradores_instance
                ).id
            )

        if "recursos" in self.initial_data:
            recursos_instance = (
                self.instance.recursos
                if self.instance and self.instance.recursos
                else None
            )
            self.initial_data["recursos"] = (
                RelevamientoService.create_or_update_recursos(
                    self.initial_data["recursos"], recursos_instance
                ).id
            )

        if "compras" in self.initial_data:
            compras_instance = (
                self.instance.compras
                if self.instance and self.instance.compras
                else None
            )
            self.initial_data["compras"] = RelevamientoService.create_or_update_compras(
                self.initial_data["compras"], compras_instance
            ).id

        if "anexo" in self.initial_data:
            anexo_instance = (
                self.instance.anexo if self.instance and self.instance.anexo else None
            )
            self.initial_data["anexo"] = RelevamientoService.create_or_update_anexo(
                self.initial_data["anexo"], anexo_instance
            ).id
        if "prestacion" in self.initial_data:
            prestacion_instance = (
                self.instance.prestacion
                if self.instance and self.instance.prestacion
                else None
            )
            self.initial_data["prestacion"] = (
                RelevamientoService.create_or_update_prestacion(
                    self.initial_data["prestacion"], prestacion_instance
                ).id
            )

        if "excepcion" in self.initial_data:
            excepcion_instance = (
                self.instance.excepcion
                if self.instance and self.instance.excepcion
                else None
            )
            self.initial_data["excepcion"] = (
                RelevamientoService.create_or_update_excepcion(
                    self.initial_data["excepcion"], excepcion_instance
                ).id
            )

        if "responsable_es_referente" in self.initial_data:
            self.initial_data["responsable_es_referente"] = (
                self.initial_data["responsable_es_referente"] == "Y"
            )

        if "responsable" in self.initial_data:
            self.initial_data["responsable"] = (
                RelevamientoService.create_or_update_responsable_relevamiento(
                    self.initial_data["responsable"],
                    self.initial_data["responsable_es_referente"],
                    self.initial_data["sisoc_id"],
                )
            )

        if "imagenes" in self.initial_data:
            self.initial_data["imagenes"] = [
                url.strip() for url in self.initial_data["imagenes"].split(",")
            ]

        return self

    class Meta:
        model = Relevamiento
        fields = "__all__"
