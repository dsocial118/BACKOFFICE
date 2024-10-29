# Generated by Django 4.0.2 on 2024-09-30 14:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('legajos', '0005_remove_dimensionfamilia_estado_civil'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProgramasLlamados',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'ProgramasLlamados',
                'verbose_name_plural': 'ProgramasLlamados',
            },
        ),
        migrations.AddField(
            model_name='llamado',
            name='fk_programas_llamados',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='legajos.programasllamados'),
        ),
        migrations.AddField(
            model_name='tipollamado',
            name='fk_programas_llamados',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='legajos.programasllamados'),
        ),
    ]
