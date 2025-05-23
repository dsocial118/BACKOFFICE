# Generated by Django 4.2.16 on 2025-05-20 12:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("admisiones", "0012_admision_observaciones"),
    ]

    operations = [
        migrations.CreateModel(
            name="AdmisionHistorial",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("campo", models.CharField(max_length=50)),
                ("valor_anterior", models.TextField(blank=True, null=True)),
                ("valor_nuevo", models.TextField(blank=True, null=True)),
                ("fecha", models.DateTimeField(auto_now_add=True)),
                (
                    "admision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historial",
                        to="admisiones.admision",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
