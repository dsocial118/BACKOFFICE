# Generated by Django 4.2.20 on 2025-06-26 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
        ("cdi", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="dias_funcionamiento",
            field=models.ManyToManyField(
                blank=True, related_name="centros", to="core.dia"
            ),
        ),
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="localidad",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.localidad",
            ),
        ),
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="meses_funcionamiento",
            field=models.ManyToManyField(
                blank=True, related_name="centros", to="core.mes"
            ),
        ),
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="municipio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.municipio",
            ),
        ),
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="provincia",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                to="core.provincia",
            ),
        ),
        migrations.AlterField(
            model_name="centrodesarrolloinfantil",
            name="turnos_funcionamiento",
            field=models.ManyToManyField(
                blank=True, related_name="centros", to="core.turno"
            ),
        ),
    ]
