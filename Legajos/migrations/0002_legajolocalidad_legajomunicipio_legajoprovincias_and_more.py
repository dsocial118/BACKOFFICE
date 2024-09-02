# Generated by Django 4.0.2 on 2024-09-02 18:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('Legajos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LegajoLocalidad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=250)),
                ('cod_bahra', models.BigIntegerField()),
                ('bahra_gid', models.IntegerField()),
                ('cod_loc', models.IntegerField()),
                ('cod_sit', models.IntegerField()),
                ('cod_entidad', models.IntegerField()),
                ('lat_gd', models.FloatField()),
                ('long_gd', models.FloatField()),
                ('long_gms', models.CharField(max_length=250)),
                ('the_geom', models.CharField(max_length=250)),
                ('departamento_id', models.IntegerField()),
                ('fuente_ubicacion', models.IntegerField()),
                ('tipo_bahra', models.IntegerField()),
                ('cod_depto', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='LegajoMunicipio',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_region', models.CharField(max_length=250)),
                ('codigo_ifam', models.CharField(max_length=250)),
                ('carta_organica', models.IntegerField()),
                ('categoria_id', models.IntegerField()),
                ('departamento_id', models.IntegerField()),
                ('iso_provincia', models.CharField(max_length=250)),
            ],
            options={
                'verbose_name': 'LegajoMunicipio',
                'verbose_name_plural': 'LegajosMunicipio',
                'ordering': ['id'],
            },
        ),
        migrations.CreateModel(
            name='LegajoProvincias',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iso_provincia', models.CharField(max_length=250)),
                ('abreviatura', models.CharField(max_length=250)),
                ('number', models.IntegerField()),
                ('nombre', models.CharField(max_length=250)),
                ('region_id', models.IntegerField()),
                ('region_territorial_id', models.IntegerField()),
                ('uuid', models.CharField(max_length=200)),
                ('status', models.IntegerField()),
            ],
            options={
                'verbose_name': 'LegajoProvincia',
                'verbose_name_plural': 'LegajosProvincia',
                'ordering': ['id'],
            },
        ),
        migrations.RemoveField(
            model_name='legajos',
            name='Provincia',
        ),
        migrations.RemoveField(
            model_name='legajos',
            name='barrio',
        ),
        migrations.RemoveField(
            model_name='legajos',
            name='localidad',
        ),
        migrations.AddIndex(
            model_name='legajoprovincias',
            index=models.Index(fields=['id'], name='Legajos_leg_id_96a920_idx'),
        ),
        migrations.AddIndex(
            model_name='legajomunicipio',
            index=models.Index(fields=['id'], name='Legajos_leg_id_4e726e_idx'),
        ),
        migrations.AddField(
            model_name='legajos',
            name='fk_localidad',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajolocalidad'),
        ),
        migrations.AddField(
            model_name='legajos',
            name='fk_municipio',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajomunicipio'),
        ),
        migrations.AddField(
            model_name='legajos',
            name='fk_provincia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='Legajos.legajoprovincias'),
        ),
    ]
