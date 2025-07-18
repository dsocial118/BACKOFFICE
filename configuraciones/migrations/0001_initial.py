# Generated by Django 4.2.20 on 2025-06-15 19:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Dia",
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
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Dia",
                "verbose_name_plural": "Dias",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Mes",
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
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Mes",
                "verbose_name_plural": "Meses",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Provincia",
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
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Provincia",
                "verbose_name_plural": "Provincia",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Sexo",
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
                ("sexo", models.CharField(max_length=10)),
            ],
            options={
                "verbose_name": "Sexo",
                "verbose_name_plural": "Sexos",
            },
        ),
        migrations.CreateModel(
            name="Turno",
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
                ("nombre", models.CharField(max_length=255)),
            ],
            options={
                "verbose_name": "Turno",
                "verbose_name_plural": "Turnos",
                "ordering": ["id"],
            },
        ),
        migrations.CreateModel(
            name="Municipio",
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
                ("nombre", models.CharField(max_length=255)),
                (
                    "provincia",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="configuraciones.provincia",
                    ),
                ),
            ],
            options={
                "verbose_name": "Municipio",
                "verbose_name_plural": "Municipio",
                "ordering": ["id"],
                "unique_together": {("nombre", "provincia")},
            },
        ),
        migrations.CreateModel(
            name="Localidad",
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
                ("nombre", models.CharField(max_length=255)),
                (
                    "municipio",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="configuraciones.municipio",
                    ),
                ),
            ],
            options={
                "verbose_name": "Localidad",
                "verbose_name_plural": "Localidad",
                "unique_together": {("nombre", "municipio")},
            },
        ),
    ]
