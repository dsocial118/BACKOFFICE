# Generated by Django 4.2.20 on 2025-07-15 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("admisiones", "0005_informetecnico_fecha_vencimiento_mandatos"),
    ]

    operations = [
        migrations.AddField(
            model_name="informetecnico",
            name="conclusiones",
            field=models.TextField(
                blank=True, null=True, verbose_name="Conclusion informe técnico"
            ),
        ),
    ]
