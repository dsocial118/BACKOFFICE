from admisiones.models.admisiones import Admision
from acompanamientos.models.hitos import Hitos, HitosIntervenciones
from acompanamientos.models.acompanamiento import InformacionRelevante, Prestacion
from intervenciones.models.intervenciones import Intervencion, SubIntervencion


class AcompanamientoService:
    @staticmethod
    def crear_hitos(intervenciones: Intervencion):
        """Crear o actualizar los hitos para una intervención.

        Args:
            intervenciones (Intervencion): Intervención a procesar.

        Returns:
            None
        """
        hitos_existente = Hitos.objects.filter(comedor=intervenciones.comedor).first()
        if intervenciones.subintervencion is None:
            intervenciones.subintervencion = SubIntervencion()
            intervenciones.subintervencion.nombre = ""
        hitos_a_actualizar = HitosIntervenciones.objects.filter(
            intervencion=intervenciones.tipo_intervencion.nombre,
            subintervencion=intervenciones.subintervencion.nombre,
        )

        if hitos_existente:
            AcompanamientoService._actualizar_hitos(hitos_existente, hitos_a_actualizar)
        else:
            nuevo_hito = Hitos.objects.create(comedor=intervenciones.comedor)
            AcompanamientoService._actualizar_hitos(nuevo_hito, hitos_a_actualizar)

    @staticmethod
    def _actualizar_hitos(hitos_objeto, hitos_a_actualizar):
        """Actualizar las banderas de un objeto :class:`Hitos`.

        Args:
            hitos_objeto (Hitos): Instancia a modificar.
            hitos_a_actualizar (QuerySet): Hitos a marcar como cumplidos.

        Returns:
            None
        """
        for hito in hitos_a_actualizar:
            for field in Hitos._meta.fields:
                if field.verbose_name == hito.hito:
                    setattr(hitos_objeto, field.name, True)
        hitos_objeto.save()

    @staticmethod
    def obtener_hitos(comedor):
        """Obtener los hitos correspondientes a un comedor.

        Args:
            comedor: Comedor para el cual se solicitan los hitos.

        Returns:
            Hitos | None
        """
        return Hitos.objects.filter(comedor=comedor).first()

    @staticmethod
    def importar_datos_desde_admision(comedor):
        """Copiar información relevante desde la admisión vinculada.

        Args:
            comedor: Comedor cuya admisión será consultada.

        Returns:
            None
        """
        admision = Admision.objects.get(comedor=comedor)
        if not admision:
            raise ValueError("No se encontró una admisión para este comedor.")
        InformacionRelevante.objects.update_or_create(
            comedor=comedor,
            defaults={
                "numero_expediente": admision.numero_expediente,
                "numero_resolucion": admision.numero_resolucion,
                "vencimiento_mandato": admision.vencimiento_mandato,
                "if_relevamiento": admision.if_relevamiento,
            },
        )

        prestaciones_admision = admision.prestaciones.all()
        Prestacion.objects.filter(comedor=comedor).delete()
        for prestacion in prestaciones_admision:
            Prestacion.objects.create(
                comedor=comedor,
                dia=prestacion.dia,
                desayuno=prestacion.desayuno,
                almuerzo=prestacion.almuerzo,
                merienda=prestacion.merienda,
                cena=prestacion.cena,
            )
