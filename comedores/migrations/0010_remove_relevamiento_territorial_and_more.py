# Generated by Django 4.2.16 on 2025-02-03 12:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "comedores",
            "0009_rename_puntuaciontotal_clasificacioncomedor_puntuacion_total",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="relevamiento",
            name="territorial",
        ),
        migrations.AddField(
            model_name="relevamiento",
            name="territorial_nombre",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="relevamiento",
            name="territorial_uid",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.DeleteModel(
            name="Territorial",
        ),
    ]
