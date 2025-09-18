from django.db import models
from core.models import Municipio, Provincia, Localidad
from django.core.validators import MaxValueValidator, MinValueValidator

class TipoOrganizacion(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Tipo de Organización"
        verbose_name_plural = "Tipos de Organización"


class TipoEntidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Tipo de Entidad"
        verbose_name_plural = "Tipos de Entidad"


class SubtipoEntidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    tipo_entidad = models.ForeignKey(
        TipoEntidad,
        on_delete=models.CASCADE,
        related_name="subtipos",
        blank=True,
        null=True,
    )

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Subtipo de Entidad"
        verbose_name_plural = "Subtipos de Entidad"


class RolFirmante(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Rol de Firmante"
        verbose_name_plural = "Roles de Firmante"


class Firmante(models.Model):
    organizacion = models.ForeignKey(
        "Organizacion", on_delete=models.CASCADE, related_name="firmantes"
    )
    nombre = models.CharField(max_length=255)
    rol = models.ForeignKey(
        RolFirmante,
        on_delete=models.PROTECT,
        related_name="firmantes",
        blank=True,
        null=True,
    )
    cuit = models.BigIntegerField(blank=True, null=True, unique=True,validators=[MinValueValidator(0), MaxValueValidator(99999999999)])

    def __str__(self):
        rol = self.rol.nombre if self.rol else "-"
        return f"{self.nombre} ({rol})"


class Aval1(models.Model):
    organizacion = models.ForeignKey(
        "Organizacion",
        on_delete=models.CASCADE,
        related_name="avales1",
        blank=True,
        null=True,
    )
    nombre = models.CharField(max_length=255, blank=True, null=True)
    cuit = models.BigIntegerField(blank=True, null=True, unique=True,validators=[MinValueValidator(0), MaxValueValidator(99999999999)])

    def __str__(self):
        return f"{self.nombre} ({self.cuit})"

    class Meta:
        verbose_name = "Aval 1"
        verbose_name_plural = "Avales 1"


class Aval2(models.Model):
    organizacion = models.ForeignKey(
        "Organizacion",
        on_delete=models.CASCADE,
        related_name="avales2",
        blank=True,
        null=True,
    )
    nombre = models.CharField(max_length=255, blank=True, null=True)
    cuit = models.BigIntegerField(unique=True, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} ({self.cuit})"

    class Meta:
        verbose_name = "Aval 2"
        verbose_name_plural = "Avales 2"


class Organizacion(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.BigIntegerField(blank=True, null=True, unique=True,validators=[MinValueValidator(0), MaxValueValidator(99999999999)])
    telefono = models.BigIntegerField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    domicilio = models.CharField(max_length=255, blank=True, null=True)
    localidad = models.ForeignKey(
        to=Localidad, on_delete=models.SET_NULL, null=True, blank=True
    )
    partido = models.CharField(max_length=255, null=True, blank=True)
    provincia = models.ForeignKey(to=Provincia, on_delete=models.PROTECT, null=True)
    municipio = models.ForeignKey(
        to=Municipio, on_delete=models.SET_NULL, null=True, blank=True
    )
    tipo_entidad = models.ForeignKey(
        TipoEntidad,
        on_delete=models.CASCADE,
        related_name="organizaciones",
        blank=True,
        null=True,
    )
    subtipo_entidad = models.ForeignKey(
        SubtipoEntidad,
        on_delete=models.CASCADE,
        related_name="organizaciones",
        blank=True,
        null=True,
    )
    fecha_vencimiento = models.DateField(blank=True, null=True)
    
    def __str__(self):
        return str(self.nombre)

    class Meta:
        ordering = ["id"]
        verbose_name = "Organizacion"
        verbose_name_plural = "Organizaciones"
