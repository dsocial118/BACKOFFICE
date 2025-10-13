from django.db import models
from users.models import User
from comedores.models import Comedor
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator


class EstadoAdmision(models.Model):
    nombre = models.CharField(max_length=15)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "estadosadmision"
        verbose_name_plural = "estadosadmisiones"


class TipoConvenio(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=["nombre"]),
        ]
        verbose_name = "tipoconvenio"
        verbose_name_plural = "tiposconvenios"


class Admision(models.Model):
    ESTADOS_LEGALES = [
        ("Enviado a Legales", "Enviado a Legales"),
        ("A Rectificar", "A Rectificar"),
        ("Rectificado", "Rectificado"),
        ("Pendiente de Validacion", "Pendiente de Validacion"),
        ("Expediente Agregado", "Expediente Agregado"),
        ("Formulario Convenio Creado", "Formulario Convenio Creado"),
        ("IF Convenio Asignado", "IF Convenio Asignado"),
        ("Formulario Disposición Creado", "Formulario Disposición Creado"),
        ("IF Disposición Asignado", "IF Disposición Asignado"),
        ("Juridicos: Validado", "Juridicos: Validado"),
        ("Juridicos: Rechazado", "Juridicos: Rechazado"),
        ("Informe SGA Generado", "Informe SGA Generado"),
        ("Convenio Firmado", "Convenio Firmado"),
        ("Acompañamiento Pendiente", "Acompañamiento Pendiente"),
        ("Archivado", "Archivado"),
        ("Informe Complementario Solicitado", "Informe Complementario Solicitado"),
        ("Informe Complementario Enviado", "Informe Complementario Enviado"),
        ("Informe Complementario: Validado", "Informe Complementario: Validado"),
        ("Finalizado", "Finalizado"),
        ("Descartado", "Descartado"),
    ]

    ESTADOS_INTERVENCION_JURIDICOS = [
        ("validado", "Validado"),
        ("rechazado", "Rechazado"),
    ]

    TIPO_ADMISION = [
        ("incorporacion", "Incorporación"),
        ("renovacion", "Renovación"),
    ]

    MOTIVO_RECHAZO_JURIDICOS = [
        ("providencia", "Por providencia"),
        ("dictamen", "Por dictamen"),
    ]
    MOTIVO_DICTAMEN = [
        ("observacion en informe técnico", "Observación en informe técnico"),
        ("observacion en proyecto de convenio", "Observación en proyecto de convenio"),
        (
            "observacion en proyecto de disposicion",
            "Observación en proyecto de disposición",
        ),
    ]

    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        null=True,
    )
    estado = models.ForeignKey(EstadoAdmision, on_delete=models.SET_NULL, null=True)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ADMISION,
        null=True,
        blank=True,
        verbose_name="Tipo de Admisión",
    )
    tipo_convenio = models.ForeignKey(
        TipoConvenio, on_delete=models.SET_NULL, null=True
    )
    num_expediente = models.CharField(max_length=255, blank=True, null=True)
    num_if = models.CharField(max_length=100, blank=True, null=True)
    legales_num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)
    enviado_legales = models.BooleanField(
        default=False, verbose_name="¿Enviado a legales?"
    )
    enviado_acompaniamiento = models.BooleanField(
        default=False, verbose_name="¿Enviado a Acompañamiento?"
    )
    estado_legales = models.CharField(
        max_length=40,
        choices=ESTADOS_LEGALES,
        null=True,
        blank=True,
        verbose_name="Estado",
    )
    intervencion_juridicos = models.CharField(
        max_length=20,
        choices=ESTADOS_INTERVENCION_JURIDICOS,
        null=True,
        blank=True,
        verbose_name="Intervención Jurídicos",
    )
    rechazo_juridicos_motivo = models.CharField(
        max_length=40,
        choices=MOTIVO_RECHAZO_JURIDICOS,
        null=True,
        blank=True,
        verbose_name="Motivo Rechazo Jurídicos",
    )
    dictamen_motivo = models.CharField(
        max_length=40,
        choices=MOTIVO_DICTAMEN,
        null=True,
        blank=True,
        verbose_name="Tipo de observación",
    )
    informe_sga = models.BooleanField(default=False, verbose_name="Estados Informe SGA")
    numero_convenio = models.CharField(max_length=100, blank=True, null=True)
    archivo_convenio = models.FileField(
        upload_to="admisiones/convenios/", null=True, blank=True
    )
    numero_disposicion = models.CharField(max_length=100, blank=True, null=True)
    archivo_disposicion = models.FileField(
        upload_to="admisiones/disposicion/", null=True, blank=True
    )
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    observaciones_reinicio_expediente = models.TextField(
        blank=True, null=True, verbose_name="Observaciones reinicio de expediente"
    )
    complementario_solicitado = models.BooleanField(
        default=False, verbose_name="Complementario Solicitado"
    )
    observaciones_informe_tecnico_complementario = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observaciones informe técnico complementario",
    )
    enviada_a_archivo = models.BooleanField(
        default=False, verbose_name="Enviada a Archivo"
    )
    motivo_descarte_expediente = models.TextField("Motivo de descarte del Expediente", null=True, blank=True)
    fecha_descarte_expediente = models.DateField("Fecha de descarte del Expediente", null=True, blank=True)
    @property
    def tipo_informe(self):
        if self.tipo_convenio_id == 1:
            return "base"
        elif self.tipo_convenio_id in [2, 3]:
            return "juridico"
        return None

    class Meta:
        indexes = [
            models.Index(fields=["comedor"]),
        ]
        verbose_name = "admisiontecnico"
        verbose_name_plural = "admisionestecnicos"
        ordering = ["-creado"]


class Documentacion(models.Model):
    nombre = models.CharField(max_length=255)
    convenios = models.ManyToManyField("TipoConvenio", blank=True)
    obligatorio = models.BooleanField(default=True)

    def __str__(self):
        return str(self.nombre) if self.nombre else "Sin nombre"


class ArchivoAdmision(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    documentacion = models.ForeignKey(
        Documentacion, on_delete=models.CASCADE, null=True, blank=True
    )
    nombre_personalizado = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Nombre personalizado"
    )
    archivo = models.FileField(
        upload_to="admisiones/admisiones_archivos/", null=True, blank=True
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ("pendiente", "Pendiente"),
            ("Documento adjunto", "Documento adjunto"),
            ("A Validar Abogado", "A Validar Abogado"),
            ("Rectificar", "Rectificar"),
            ("Aceptado", "Aceptado"),
        ],
        default="pendiente",
    )
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    numero_gde = models.CharField(
        "Número de GDE",
        max_length=50,
        blank=True,
        null=True,
        help_text="Número de expediente GDE asignado por el técnico después de la carga en sistema externo",
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateField(auto_now=True, null=True, blank=True)

    def delete(self, *args, **kwargs):
        if self.rectificar:
            raise ValidationError(
                "No se puede eliminar un registro marcado como 'Rectificar'."
            )
        super().delete(*args, **kwargs)

    @property
    def es_personalizado(self):
        return self.documentacion_id is None

    def __str__(self):
        if self.documentacion:
            nombre = self.documentacion.nombre
        else:
            nombre = self.nombre_personalizado or "Documento sin nombre"
        return f"{self.admision.id} - {nombre}"


class InformeTecnico(models.Model):
    ESTADOS = [
        ("Iniciado", "Iniciado"),
        ("Para revision", "Para revisión"),
        ("Validado", "Validado"),
        ("A subsanar", "A subsanar"),
    ]
    TIPO_CHOICES = [
        ("base", "Base"),
        ("juridico", "Jurídico"),
    ]
    ESTADOS_FORM = [
        ("borrador", "Borrador"),
        ("finalizado", "Finalizado"),
    ]

    estado_formulario = models.CharField(
        max_length=20, choices=ESTADOS_FORM, default="borrador"
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    # Campos comunes de los informes tecnicos.

    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)
    expediente_nro = models.CharField("Número Expediente", max_length=100)

    nombre_organizacion = models.CharField(
        "Nombre de la Organización Solicitante", max_length=255
    )
    domicilio_organizacion = models.CharField(
        "Domicilio de la Organización Solicitante", max_length=255
    )
    localidad_organizacion = models.CharField(
        "Localidad de la Organización Solicitante", max_length=255
    )
    partido_organizacion = models.CharField(
        "Partido de la Organización Solicitante", max_length=255
    )
    provincia_organizacion = models.CharField(
        "Provincia de la Organización Solicitante", max_length=255
    )
    telefono_organizacion = models.CharField(
        "Teléfono de la Organización Solicitante", max_length=50
    )
    mail_organizacion = models.EmailField("Mail de la Organización Solicitante")
    cuit_organizacion = models.CharField(
        "CUIT de la Organización Solicitante", max_length=20
    )

    representante_nombre = models.CharField(
        "Nombre y Apellido del Representante", max_length=255
    )
    representante_cargo = models.CharField("Cargo del Representante", max_length=100)
    representante_dni = models.CharField("DNI del Representante", max_length=20)

    tipo_espacio = models.CharField(
        "Tipo de Espacio Comunitario",
        max_length=50,
        choices=[
            ("Comedor", "Comedor"),
            ("Merendero", "Merendero"),
            ("Punto de Entrega", "Punto de Entrega"),
            ("Comedor y Merendero", "Comedor y Merendero"),
        ],
    )
    nombre_espacio = models.CharField("Nombre del Comedor/Merendero", max_length=255)
    domicilio_espacio = models.CharField(
        "Domicilio del Comedor/Merendero", max_length=255
    )
    domicilio_electronico_espacio = models.EmailField("Domicilio electronico constituido del Comedor/Merendero", null=True, blank=True)
    barrio_espacio = models.CharField("Barrio del Comedor/Merendero", max_length=255)
    localidad_espacio = models.CharField(
        "Localidad del Comedor/Merendero", max_length=255
    )
    partido_espacio = models.CharField("Partido del Comedor/Merendero", max_length=255)
    provincia_espacio = models.CharField(
        "Provincia del Comedor/Merendero", max_length=255
    )

    responsable_tarjeta_nombre = models.CharField(
        "Nombre del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_cuit = models.CharField(
        "CUIL/CUIT del Responsable de la Tarjeta", max_length=255, null=True, blank=True
    )
    responsable_tarjeta_dni = models.CharField(
        "DNI del Responsable de la Tarjeta", max_length=20
    )
    responsable_tarjeta_domicilio = models.CharField(
        "Domicilio del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_localidad = models.CharField(
        "Localidad del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_provincia = models.CharField(
        "Provincia del Responsable de la Tarjeta", max_length=255
    )
    responsable_tarjeta_telefono = models.CharField(
        "Teléfono del Responsable de la Tarjeta", max_length=50
    )
    responsable_tarjeta_mail = models.EmailField("Mail del Responsable de la Tarjeta")
    nota_gde_if = models.CharField("Nota GDE IF", max_length=255)
    constancia_subsidios_dnsa = models.CharField(
        "Constancia IF RTA DNSA sobre subsidios", max_length=255
    )
    constancia_subsidios_pnud = models.CharField(
        "Constancia IF RTA PNUD sobre subsidios", max_length=255
    )
    partido_poblacion_destinataria = models.CharField(
        "Partido donde se ubica la población destinataria", max_length=255
    )
    provincia_poblacion_destinataria = models.CharField(
        "Provincia donde se ubica la población destinataria", max_length=255
    )

    if_relevamiento = models.CharField("IF de relevamiento territorial", max_length=255)
    fecha_vencimiento_mandatos = models.DateField(
        "Fecha de vencimiento de mandatos", null=True, blank=True
    )

    # Exclusivos de organizacion de Base
    declaracion_jurada_recepcion_subsidios = models.CharField(
        "Declaración Jurada sobre recepción de subsidios nacionales", max_length=255
    )
    constancia_inexistencia_percepcion_otros_subsidios = models.CharField(
        "Constancia de inexistencia de percepción de otros subsidios nacionales",
        max_length=255,
    )
    organizacion_avalista_1 = models.CharField(
        "Organización Avalista 1", max_length=255
    )
    organizacion_avalista_2 = models.CharField(
        "Organización Avalista 2", max_length=255
    )
    material_difusion_vinculado = models.CharField(
        "Material de difusión vinculado", max_length=255
    )

    # Exclusivos de organizacion juridica
    validacion_registro_nacional = models.CharField(
        "Validación Registro Nacional Comedores/Merenderos", max_length=255
    )
    IF_relevamiento_territorial = models.CharField(
        "IF de relevamiento territorial", max_length=255
    )
    conclusiones = models.TextField("Aplicación de Criterios", null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        verbose_name="Estado del Informe",
    )
    solicitudes_desayuno_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_desayuno_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_almuerzo_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_almuerzo_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_merienda_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_merienda_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    solicitudes_cena_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    solicitudes_cena_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    total_acreditaciones = models.CharField(
        "Total de acreditaciones a Producir", max_length=150, null=True, blank=True
    )
    plazo_ejecucion = models.CharField(
        "Plazo de Ejecución", max_length=150, null=True, blank=True
    )

    # Prestaciones aprobadas (antes en Anexo)
    aprobadas_desayuno_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_desayuno_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_almuerzo_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_almuerzo_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_merienda_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_merienda_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    aprobadas_cena_lunes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_martes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_jueves = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_viernes = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_sabado = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    aprobadas_cena_domingo = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    # Campos exclusivos de Renovación.
    resolucion_de_pago_1 = models.CharField(
        "Resolución de pago 1", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_2 = models.CharField(
        "Resolución de pago 2", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_3 = models.CharField(
        "Resolución de pago 3", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_4 = models.CharField(
        "Resolución de pago 4", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_5 = models.CharField(
        "Resolución de pago 5", max_length=150, null=True, blank=True
    )
    resolucion_de_pago_6 = models.CharField(
        "Resolución de pago 6", max_length=150, null=True, blank=True
    )
    monto_1 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    monto_2 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    monto_3 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    monto_4 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    monto_5 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    monto_6 = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f"{self.nombre_organizacion} - {self.expediente_nro}"


class CampoASubsanar(models.Model):
    informe = models.ForeignKey(InformeTecnico, on_delete=models.CASCADE)
    campo = models.CharField(max_length=100)


class ObservacionGeneralInforme(models.Model):
    informe = models.OneToOneField(InformeTecnico, on_delete=models.CASCADE)
    texto = models.TextField()


class Anexo(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.SET_NULL, null=True)

    expediente = models.CharField("Expediente", max_length=100, null=True, blank=True)
    efector = models.CharField(
        "Efector (nombre)", max_length=100, null=True, blank=True
    )
    tipo_espacio = models.CharField(
        "Tipo (Comedor / Merendero)",
        max_length=50,
        choices=[
            ("Comedor", "Comedor"),
            ("Merendero", "Merendero"),
            ("Comedor y Merendero", "Comedor y Merendero"),
        ],
        null=True,
        blank=True,
    )
    domicilio = models.CharField("Domicilio", max_length=150, null=True, blank=True)
    barrio = models.CharField("Barrio", max_length=50, null=True, blank=True)
    mail = models.EmailField("Correo Electrónico", null=True, blank=True)
    responsable_apellido = models.CharField(
        "Apellido", max_length=150, null=True, blank=True
    )
    responsable_nombre = models.CharField(
        "Nombre", max_length=150, null=True, blank=True
    )
    responsable_cuit = models.BigIntegerField(
        "CUIT / CUIL",
        validators=[MinValueValidator(10**10), MaxValueValidator(99999999999)],
        null=True,
        blank=True,
    )
    responsable_domicilio = models.CharField(
        "Domicilio", max_length=150, null=True, blank=True
    )
    responsable_mail = models.EmailField("Correo Electrónico", null=True, blank=True)
    total_acreditaciones = models.CharField(
        "Total de acreditaciones a Producir", max_length=150, null=True, blank=True
    )
    plazo_ejecucion = models.CharField(
        "Plazo de Ejecución", max_length=150, null=True, blank=True
    )

    desayuno_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    desayuno_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    desayuno_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    almuerzo_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    almuerzo_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    almuerzo_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    merienda_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_miercoles = models.IntegerField(
        default=0, validators=[MinValueValidator(0)]
    )
    merienda_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    merienda_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    cena_lunes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_martes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_miercoles = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_jueves = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_viernes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_sabado = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    cena_domingo = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"Anexo #{self.id}"


class InformeTecnicoPDF(models.Model):
    admision = models.OneToOneField(
        "Admision", on_delete=models.CASCADE, related_name="informe_pdf"
    )
    tipo = models.CharField(
        max_length=20, choices=[("base", "Base"), ("juridico", "Jurídico")]
    )
    informe_id = models.PositiveIntegerField()
    comedor = models.ForeignKey(
        Comedor,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_informes_tecnicos_pdf",
    )
    archivo = models.FileField(upload_to="admisiones/informes_tecnicos/pdf")
    archivo_docx = models.FileField(
        upload_to="admisiones/informes_tecnicos/docx", null=True, blank=True
    )
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - PDF Admision #{self.admision_id}"


class AdmisionHistorial(models.Model):
    admision = models.ForeignKey(
        "Admision", on_delete=models.CASCADE, related_name="historial"
    )
    campo = models.CharField(max_length=50)
    valor_anterior = models.TextField(blank=True, null=True)
    valor_nuevo = models.TextField(blank=True, null=True)
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_historial",
    )
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.campo} cambiado por {self.usuario} el {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class FormularioProyectoDisposicion(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="admisiones_proyecto_disposicion",
    )
    tipo = models.CharField(
        max_length=20,
        choices=[("incorporacion", "Incorporación"), ("renovacion", "Renovación")],
    )
    archivo = models.FileField(
        upload_to="admisiones/formularios_disposicion/pdf", null=True
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/formularios_disposicion/docx", null=True
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_formularios_disposicion",
    )

    def __str__(self):
        return f"Formulario Proyecto de Disposicion de {self.admision} por {self.creado_por}"


class FormularioProyectoDeConvenio(models.Model):
    admision = models.ForeignKey(
        "Admision",
        on_delete=models.CASCADE,
        related_name="admisiones_proyecto_convenio",
    )
    archivo = models.FileField(
        upload_to="admisiones/formularios_convenio/pdf", null=True
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/formularios_convenio/docx", null=True
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_formularios_convenio",
    )

    def __str__(self):
        return (
            f"Formulario Proyecto de Convenio de {self.admision} por {self.creado_por}"
        )


class DocumentosExpediente(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(max_length=255, blank=True, null=True)
    archivo = models.FileField(upload_to="admisiones/expediente", null=True, blank=True)
    rectificar = models.BooleanField(default=False, verbose_name="Rectificar")
    observaciones = models.TextField(
        blank=True, null=True, verbose_name="Observaciones"
    )
    num_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.admision.id}"


class InformeComplementario(models.Model):
    ESTADOS = [
        ("borrador", "Borrador"),
        ("enviado_validacion", "Enviado a Validación"),
        ("validado", "Validado"),
        ("rectificar", "A Rectificar"),
    ]

    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    informe_tecnico = models.ForeignKey(InformeTecnico, on_delete=models.CASCADE)
    pdf = models.FileField(upload_to="admisiones/informes_complementarios/", null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="borrador")
    observaciones_legales = models.TextField(
        blank=True, null=True, verbose_name="Observaciones de Legales"
    )
    creado = models.DateField(auto_now_add=True, null=True, blank=True)
    modificado = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="admisiones_informes_complementarios",
    )


class InformeComplementarioCampos(models.Model):
    campo = models.CharField(max_length=255, blank=False, null=False)
    value = models.CharField(max_length=255, blank=False, null=False)
    informe_complementario = models.ForeignKey(
        InformeComplementario, on_delete=models.CASCADE
    )


class InformeTecnicoComplementarioPDF(models.Model):
    admision = models.ForeignKey(Admision, on_delete=models.CASCADE)
    informe_complementario = models.OneToOneField(
        InformeComplementario, on_delete=models.CASCADE, related_name="pdf_final"
    )
    tipo = models.CharField(
        max_length=20, choices=[("base", "Base"), ("juridico", "Jurídico")]
    )
    archivo = models.FileField(
        upload_to="admisiones/informes_complementarios_final/pdf"
    )
    archivo_docx = models.FileField(
        upload_to="admisiones/informes_complementarios_final/docx",
        null=True,
        blank=True,
    )
    numero_if = models.CharField(max_length=100, blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PDF Complementario Final - Admision #{self.admision_id}"
