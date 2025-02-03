# Generated by Django 4.2.16 on 2025-01-28 15:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0004_tipoaccesocomedor_tipodistanciatransporte_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoriaComedor",
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
                ("puntuacionMin", models.IntegerField()),
                ("puntuacionMax", models.IntegerField()),
            ],
            options={
                "verbose_name": "Categoria de Comedor",
                "verbose_name_plural": "Categorias de Comedor",
            },
        ),
        migrations.CreateModel(
            name="ClasificacionComedor",
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
                ("puntuacionTotal", models.IntegerField()),
                (
                    "categoria",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="comedores.categoriacomedor",
                    ),
                ),
                (
                    "comedor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="comedores.comedor",
                    ),
                ),
                (
                    "relevamiento",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="comedores.relevamiento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Clasificacion de Comedor",
                "verbose_name_plural": "Clasificaciones de Comedor",
            },
        ),
    ]
