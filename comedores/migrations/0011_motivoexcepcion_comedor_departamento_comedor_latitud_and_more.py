# Generated by Django 4.2.16 on 2025-02-06 16:38

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0010_remove_relevamiento_territorial_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="MotivoExcepcion",
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
                ("nombre", models.CharField(max_length=255, unique=True)),
            ],
            options={
                "verbose_name": "Motivo de excepcion",
                "verbose_name_plural": "Motivos de excepcion",
            },
        ),
        migrations.AddField(
            model_name="comedor",
            name="departamento",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="latitud",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-90),
                    django.core.validators.MaxValueValidator(90),
                ],
            ),
        ),
        migrations.AddField(
            model_name="comedor",
            name="longitud",
            field=models.FloatField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(-180),
                    django.core.validators.MaxValueValidator(180),
                ],
            ),
        ),
        migrations.AddField(
            model_name="comedor",
            name="lote",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="manzana",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="comedor",
            name="piso",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name="Excepcion",
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
                ("descripcion", models.TextField(blank=True, null=True)),
                (
                    "latitud",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-90),
                            django.core.validators.MaxValueValidator(90),
                        ],
                    ),
                ),
                (
                    "longitud",
                    models.FloatField(
                        blank=True,
                        null=True,
                        validators=[
                            django.core.validators.MinValueValidator(-180),
                            django.core.validators.MaxValueValidator(180),
                        ],
                    ),
                ),
                ("adjuntos", models.JSONField(blank=True, default=list, null=True)),
                ("firma", models.CharField(blank=True, max_length=600, null=True)),
                (
                    "motivo",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.motivoexcepcion",
                    ),
                ),
            ],
            options={
                "verbose_name": "Excepcion de comedor",
                "verbose_name_plural": "Excepciones de comedor",
            },
        ),
        migrations.AddField(
            model_name="relevamiento",
            name="excepcion",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="comedores.excepcion",
            ),
        ),
    ]
