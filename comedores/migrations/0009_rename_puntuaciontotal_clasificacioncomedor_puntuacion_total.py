# Generated by Django 4.2.16 on 2025-01-31 15:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "comedores",
            "0008_rename_puntuacionmax_categoriacomedor_puntuacion_max_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="clasificacioncomedor",
            old_name="puntuacionTotal",
            new_name="puntuacion_total",
        ),
    ]
