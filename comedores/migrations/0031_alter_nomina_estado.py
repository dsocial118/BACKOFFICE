# Generated by Django 4.2.16 on 2025-05-09 13:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0003_rename_estadosintervencion_estadointervencion"),
        ("comedores", "0030_alter_nomina_estado_delete_estadosintervencion_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="nomina",
            name="estado",
            field=models.ForeignKey(
                default=1,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="ciudadanos.estadointervencion",
            ),
        ),
    ]
