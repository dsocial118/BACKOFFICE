# Generated by Django 4.2.16 on 2025-03-18 16:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "comedores",
            "0018_rename_registran_entrega_bolsones_puntoentregas_registran_entrega_bolsones",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="anexo",
            name="servicio_internet",
            field=models.BooleanField(default=True),
        ),
    ]
