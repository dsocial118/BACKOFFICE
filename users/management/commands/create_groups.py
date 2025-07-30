from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = "Crea los grupos de usuario predeterminados"

    def handle(self, *args, **kwargs):
        groups = [
            "Admin",
            "Comedores",
            "Organizaciones",
            "CDI",
            "Ciudadanos",
            "Tecnico Comedor",
            "Abogado Dupla",
            "Area Contable",
            "Area Legales",
            "Comedores Listar",
            "Comedores Crear",
            "Comedores Ver",
            "Comedores Editar",
            "Comedores Eliminar",
            "Comedores Relevamiento Ver",
            "Comedores Relevamiento Crear",
            "Comedores Relevamiento Detalle",
            "Comedores Relevamiento Editar",
            "Comedores Observaciones Crear",
            "Comedores Observaciones Detalle",
            "Comedores Observaciones Editar",
            "Comedores Observaciones Eliminar",
            "Comedores Intervencion Ver",
            "Comedores Intervencion Crear",
            "Comedores Intervencion Editar",
            "Comedores Intervenciones Detalle",
            "Comedores Nomina Ver",
            "Comedores Nomina Crear",
            "Comedores Nomina Editar",
            "Comedores Nomina Borrar",
            "Comedores Dupla Asignar",
            "Acompanamiento Detalle",
            "Acompanamiento Listar",
            "Usuario Crear",
            "Usuario Eliminar",
            "Usuario Editar",
            "Usuario Listar",
            "Grupos Ver",
            "Admin Ver Expedientes",
            "Técnico Ver Tareas Asignadas",
            "Provincia Ver Estado Pago",
            "Provincia Crear Expediente",
            "Provincia Ver Lista Aprobados",
            "Provincia Cargar Formulario",
            "Provincia Finalizar Expediente",
            "Admin Asignar Técnico",
            "Técnico Subir Cruces",
            "Técnico Validar Resultado Cruce",
            "Técnico Registrar Informe Pago", "ReferenteCentro",
            "CDF SSE",
            "TecnicoCeliaquia",
            "CoordinadorCeliaquia",
            "ProvinciaCeliaquia",
        ]
        self.stdout.write(self.style.SUCCESS(f"Creando grupos de usuario..."))
        for group_name in groups:
            _group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grupo "{group_name}" creado'))
