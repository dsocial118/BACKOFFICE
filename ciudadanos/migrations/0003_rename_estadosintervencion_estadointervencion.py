# Generated by Django 4.2.16 on 2025-04-14 15:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ciudadanos", "0002_alter_ciudadano_sexo_delete_sexo"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="EstadosIntervencion",
            new_name="EstadoIntervencion",
        ),
    ]
