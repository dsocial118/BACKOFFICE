# Generated by Django 4.2.16 on 2024-12-16 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("comedores", "0003_alter_comedor_localidad_alter_comedor_municipio_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comedor",
            name="gestionar_uid",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="relevamiento",
            name="gestionar_uid",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
