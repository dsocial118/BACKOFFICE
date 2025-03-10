# Generated by Django 4.2.16 on 2025-01-24 15:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0003_comedor_organizacion"),
    ]

    operations = [
        migrations.CreateModel(
            name="TipoAccesoComedor",
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
                "verbose_name": "Tipo de acceso al comedor",
                "verbose_name_plural": "Tipos de acceso al comedor",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TipoDistanciaTransporte",
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
                "verbose_name": "Distancia de transporte",
                "verbose_name_plural": "Distancias de transporte",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TipoFrecuenciaInsumos",
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
                "verbose_name": "Frecuencia de insumos recibidos",
                "verbose_name_plural": "Frecuencias de insumos recibidos",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TipoInsumos",
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
                "verbose_name": "Tipo de insumo recibido",
                "verbose_name_plural": "Tipos de insumos recibidos",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="TipoTecnologia",
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
                "verbose_name": "Tipo de tecnologia",
                "verbose_name_plural": "Tipos de tecnologia",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Anexo",
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
                ("comedor_merendero", models.BooleanField(default=False)),
                ("insumos_organizacion", models.BooleanField(default=False)),
                ("servicio_internet", models.BooleanField(default=False)),
                ("zona_inundable", models.BooleanField(default=False)),
                ("actividades_jardin_maternal", models.BooleanField(default=False)),
                ("actividades_jardin_infantes", models.BooleanField(default=False)),
                ("apoyo_escolar", models.BooleanField(default=False)),
                ("alfabetizacion_terminalidad", models.BooleanField(default=False)),
                ("capacitaciones_talleres", models.BooleanField(default=False)),
                ("promocion_salud", models.BooleanField(default=False)),
                ("actividades_discapacidad", models.BooleanField(default=False)),
                ("necesidades_alimentarias", models.BooleanField(default=False)),
                ("actividades_recreativas", models.BooleanField(default=False)),
                ("actividades_culturales", models.BooleanField(default=False)),
                ("emprendimientos_productivos", models.BooleanField(default=False)),
                ("actividades_religiosas", models.BooleanField(default=False)),
                ("actividades_huerta", models.BooleanField(default=False)),
                ("espacio_huerta", models.BooleanField(default=False)),
                ("otras_actividades", models.BooleanField(default=False)),
                ("cuales_otras_actividades", models.TextField(blank=True, null=True)),
                (
                    "veces_recibio_insumos_2024",
                    models.IntegerField(
                        default=0,
                        verbose_name="¿Cuántas veces recibió estos insumos en el año 2024?",
                    ),
                ),
                (
                    "acceso_comedor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.tipoaccesocomedor",
                        verbose_name="Al comedor se accede por...",
                    ),
                ),
                (
                    "distancia_transporte",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.tipodistanciatransporte",
                        verbose_name="¿Qué distancia hay desde el comedor al transporte público más cercano?",
                    ),
                ),
                (
                    "frecuencia_insumo",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.tipofrecuenciainsumos",
                        verbose_name="¿Con qué frecuencia recibió estos insumos?",
                    ),
                ),
                (
                    "tecnologia",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.tipotecnologia",
                        verbose_name="¿El espacio comunitario cuenta con?",
                    ),
                ),
                (
                    "tipo_insumo",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        to="comedores.tipoinsumos",
                        verbose_name="¿Qué tipo de insumo recibió?",
                    ),
                ),
            ],
            options={
                "verbose_name": "Anexo",
                "verbose_name_plural": "Anexos",
            },
        ),
        migrations.AddField(
            model_name="relevamiento",
            name="anexo",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="comedores.anexo",
            ),
        ),
    ]
