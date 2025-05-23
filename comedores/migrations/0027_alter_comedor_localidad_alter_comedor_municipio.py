# Generated by Django 4.2.16 on 2025-04-22 07:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        (
            "configuraciones",
            "0009_alter_localidad_municipio_alter_municipio_provincia_and_more",
        ),
        ("comedores", "0026_comedor_dupla_comedor_estado"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comedor",
            name="localidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="configuraciones.localidad",
            ),
        ),
        migrations.AlterField(
            model_name="comedor",
            name="municipio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="configuraciones.municipio",
            ),
        ),
    ]
