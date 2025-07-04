from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea un superusuario solo si no existe y si DEBUG=True"

    def handle(self, *args, **kwargs):
        if not settings.DEBUG:
            self.stdout.write(
                self.style.ERROR(
                    "No se puede crear el superusuario porque DEBUG=False."
                )
            )
            return

        user = get_user_model()

        username = "1"
        email = "1@gmail.com"
        password = "1"

        self.stdout.write(self.style.SUCCESS("Creando usuarios..."))
        if not user.objects.filter(username=username).exists():
            user.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.stdout.write(self.style.SUCCESS(f"Superusuario '{username}' creado."))
