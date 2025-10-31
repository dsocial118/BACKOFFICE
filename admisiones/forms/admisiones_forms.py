from django import forms

from admisiones.models.admisiones import (
    Admision,
    InformeTecnico,
    FormularioProyectoDisposicion,
    FormularioProyectoDeConvenio,
    DocumentosExpediente,
    ArchivoAdmision,
)


def _ultimo_numero_gde(admision, documentacion_nombre):
    if not admision:
        return None

    return (
        ArchivoAdmision.objects.filter(
            admision=admision,
            documentacion__nombre=documentacion_nombre,
        )
        .exclude(numero_gde__isnull=True)
        .exclude(numero_gde="")
        .order_by("-modificado", "-id")
        .values_list("numero_gde", flat=True)
        .first()
    )


class AdmisionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = "__all__"


class InformeTecnicoJuridicoForm(forms.ModelForm):
    class Meta:
        model = InformeTecnico
        exclude = [
            "admision",
            "estado",
            "estado_formulario",
            "tipo",
            "declaracion_jurada_recepcion_subsidios",
            "constancia_inexistencia_percepcion_otros_subsidios",
            "organizacion_avalista_1",
            "organizacion_avalista_2",
            "material_difusion_vinculado",
        ]
        labels = {
            "IF_relevamiento_territorial": "IF Relevamiento Territorial",
            "if_relevamiento": "IF Relevamiento",
        }
        widgets = {
            "fecha_vencimiento_mandatos": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            )
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        self.require_full = kwargs.pop("require_full", False)
        super().__init__(*args, **kwargs)

        if "fecha_vencimiento_mandatos" in self.fields:
            self.fields["fecha_vencimiento_mandatos"].input_formats = ["%Y-%m-%d"]

        # Hacer campos obligatorios solo si require_full es True,
        # dejando opcionales las resoluciones y montos (salvo renovaciones).
        campos_pago_opcionales = {f"resolucion_de_pago_{i}" for i in range(1, 7)}
        campos_pago_opcionales.update({f"monto_{i}" for i in range(1, 7)})

        for name, field in self.fields.items():
            if name in campos_pago_opcionales:
                field.required = False
            else:
                field.required = self.require_full

        # Hacer obligatorios los campos de renovación si require_full es True y el tipo de admisión es 'renovacion'
        if admision and admision.tipo == "renovacion" and self.require_full:
            for i in range(1, 7):
                if f"resolucion_de_pago_{i}" in self.fields:
                    self.fields[f"resolucion_de_pago_{i}"].required = True
                if f"monto_{i}" in self.fields:
                    self.fields[f"monto_{i}"].required = True

        for name, field in self.fields.items():
            if name.startswith("solicitudes_") or name.startswith("aprobadas_"):
                field.label = False
                field.widget.attrs["aria-label"] = ""
                field.widget.attrs["placeholder"] = ""
                field.widget.attrs["class"] = (
                    field.widget.attrs.get("class", "")
                    + " form-control form-control-sm text-center"
                ).strip()

        if admision:
            comedor = admision.comedor
            organizacion = comedor.organizacion if comedor else None

            self.fields["expediente_nro"].initial = admision.num_expediente
            calle = getattr(comedor, "calle", "")
            numero = getattr(comedor, "numero", "")
            referente = getattr(comedor, "referente", None)

            self.fields["nombre_espacio"].initial = comedor.nombre
            self.fields["domicilio_espacio"].initial = f"{calle} {numero}".strip()
            self.fields["barrio_espacio"].initial = getattr(comedor, "barrio", "")
            self.fields["localidad_espacio"].initial = getattr(comedor, "localidad", "")
            self.fields["partido_espacio"].initial = getattr(comedor, "partido", "")
            self.fields["provincia_espacio"].initial = getattr(comedor, "provincia", "")
            self.fields["tipo_espacio"].initial = getattr(comedor, "tipocomedor", "")
            self.fields["total_acreditaciones"].initial = "6"
            self.fields["plazo_ejecucion"].initial = "6 meses"
            self.fields["nota_gde_if"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion__nombre="Nota de solicitud e Inclusión al Programa",
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            self.fields["constancia_subsidios_dnsa"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion__nombre="Acta Solicitud de Subsidio",
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            self.fields["constancia_subsidios_pnud"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision, documentacion__nombre="Respuesta Memo PNUD"
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            if "validacion_registro_nacional" in self.fields:
                self.fields["validacion_registro_nacional"].initial = (
                    ArchivoAdmision.objects.filter(
                        admision=admision, documentacion__nombre="Validación RENACOM"
                    )
                    .values_list("numero_gde", flat=True)
                    .first()
                )
            if "if_relevamiento" in self.fields:
                self.fields["if_relevamiento"].initial = _ultimo_numero_gde(
                    admision,
                    "Relevamiento al Programa PAC",
                )
            # ESTO SE COMENTIO POR QUE NO QUIEREN QUE SE PREGARGE EL REFERENTE PERO PUEDE CAMBIAR
            # if referente:
            #    self.fields["representante_nombre"].initial = (
            #        f"{referente.nombre or ''} {referente.apellido or ''}".strip()
            #    )
            #    self.fields["representante_dni"].initial = referente.documento or ""
            #    self.fields["representante_cargo"].initial = referente.funcion or ""

            if organizacion:
                self.fields["nombre_organizacion"].initial = organizacion.nombre
                self.fields["cuit_organizacion"].initial = organizacion.cuit
                self.fields["mail_organizacion"].initial = organizacion.email
                self.fields["telefono_organizacion"].initial = organizacion.telefono
                self.fields["domicilio_organizacion"].initial = organizacion.domicilio
                self.fields["localidad_organizacion"].initial = organizacion.localidad
                self.fields["provincia_organizacion"].initial = organizacion.provincia
                self.fields["partido_organizacion"].initial = organizacion.partido

                if not self.instance.fecha_vencimiento_mandatos:
                    self.fields["fecha_vencimiento_mandatos"].initial = (
                        organizacion.fecha_vencimiento
                    )


class InformeTecnicoBaseForm(forms.ModelForm):
    class Meta:
        model = InformeTecnico
        exclude = [
            "admision",
            "estado",
            "estado_formulario",
            "tipo",
            "validacion_registro_nacional",
            "IF_relevamiento_territorial",
        ]
        widgets = {
            "fecha_vencimiento_mandatos": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": "form-control",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        admision = kwargs.pop("admision", None)
        self.require_full = kwargs.pop("require_full", False)
        super().__init__(*args, **kwargs)

        if "fecha_vencimiento_mandatos" in self.fields:
            self.fields["fecha_vencimiento_mandatos"].input_formats = ["%Y-%m-%d"]

        # Hacer campos obligatorios solo si require_full es True,
        # dejando opcionales las resoluciones y montos (salvo renovaciones).
        campos_pago_opcionales = {f"resolucion_de_pago_{i}" for i in range(1, 7)}
        campos_pago_opcionales.update({f"monto_{i}" for i in range(1, 7)})

        for name, field in self.fields.items():
            if name in campos_pago_opcionales:
                field.required = False
            else:
                field.required = self.require_full

        # Hacer obligatorios los campos de renovación si require_full es True y el tipo de admisión es 'renovacion'
        if admision and admision.tipo == "renovacion" and self.require_full:
            for i in range(1, 7):
                if f"resolucion_de_pago_{i}" in self.fields:
                    self.fields[f"resolucion_de_pago_{i}"].required = True
                if f"monto_{i}" in self.fields:
                    self.fields[f"monto_{i}"].required = True

        for name, field in self.fields.items():
            if name.startswith("solicitudes_") or name.startswith("aprobadas_"):
                field.label = False
                field.widget.attrs["aria-label"] = ""
                field.widget.attrs["placeholder"] = ""

        if admision:
            comedor = admision.comedor
            organizacion = comedor.organizacion if comedor else None

            self.fields["expediente_nro"].initial = admision.num_expediente
            calle = getattr(comedor, "calle", "")
            numero = getattr(comedor, "numero", "")
            referente = getattr(comedor, "referente", None)

            self.fields["nombre_espacio"].initial = comedor.nombre
            self.fields["domicilio_espacio"].initial = f"{calle} {numero}".strip()
            self.fields["barrio_espacio"].initial = getattr(comedor, "barrio", "")
            self.fields["localidad_espacio"].initial = getattr(comedor, "localidad", "")
            self.fields["partido_espacio"].initial = getattr(comedor, "partido", "")
            self.fields["provincia_espacio"].initial = getattr(comedor, "provincia", "")
            self.fields["tipo_espacio"].initial = getattr(comedor, "tipocomedor", "")
            self.fields["total_acreditaciones"].initial = "6"
            self.fields["plazo_ejecucion"].initial = "6 meses"
            self.fields["nota_gde_if"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion__nombre="Nota de solicitud e Inclusión al Programa",
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            self.fields["constancia_subsidios_dnsa"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision,
                    documentacion__nombre="Acta Solicitud de Subsidio",
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            self.fields["constancia_subsidios_pnud"].initial = (
                ArchivoAdmision.objects.filter(
                    admision=admision, documentacion__nombre="Respuesta Memo PNUD"
                )
                .values_list("numero_gde", flat=True)
                .first()
            )
            if "validacion_registro_nacional" in self.fields:
                self.fields["validacion_registro_nacional"].initial = (
                    ArchivoAdmision.objects.filter(
                        admision=admision, documentacion__nombre="Validación RENACOM"
                    )
                    .values_list("numero_gde", flat=True)
                    .first()
                )
            if "if_relevamiento" in self.fields:
                self.fields["if_relevamiento"].initial = _ultimo_numero_gde(
                    admision,
                    "Relevamiento al Programa PAC",
                )
            # ESTO SE COMENTIO POR QUE NO QUIEREN QUE SE PREGARGE EL REFERENTE PERO PUEDE CAMBIAR
            # if referente:
            #    self.fields["representante_nombre"].initial = (
            #        f"{referente.nombre or ''} {referente.apellido or ''}".strip()
            #    )
            #    self.fields["representante_dni"].initial = referente.documento or ""
            #    self.fields["representante_cargo"].initial = referente.funcion or ""

            if organizacion:
                self.fields["nombre_organizacion"].initial = organizacion.nombre
                self.fields["cuit_organizacion"].initial = organizacion.cuit
                self.fields["mail_organizacion"].initial = organizacion.email
                self.fields["telefono_organizacion"].initial = organizacion.telefono
                self.fields["domicilio_organizacion"].initial = organizacion.domicilio
                self.fields["localidad_organizacion"].initial = organizacion.localidad
                self.fields["provincia_organizacion"].initial = organizacion.provincia
                self.fields["partido_organizacion"].initial = organizacion.partido

                if not self.instance.fecha_vencimiento_mandatos:
                    self.fields["fecha_vencimiento_mandatos"].initial = (
                        organizacion.fecha_vencimiento
                    )


class InformeTecnicoEstadoForm(forms.Form):
    ESTADOS = [
        ("A subsanar", "A subsanar"),
        ("Validado", "Validado"),
    ]
    estado = forms.ChoiceField(choices=ESTADOS, required=True)
    campos_a_subsanar = forms.MultipleChoiceField(
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=[],
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs):
        campos_choices = kwargs.pop("campos_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["campos_a_subsanar"].choices = campos_choices

    def clean(self):
        cleaned_data = super().clean()
        estado = cleaned_data.get("estado")
        campos = cleaned_data.get("campos_a_subsanar")

        if estado == "A subsanar" and not campos:
            raise forms.ValidationError(
                "Debe marcar al menos un campo para subsanar cuando el estado es 'A subsanar'."
            )
        return cleaned_data


class CaratularForm(forms.ModelForm):

    num_expediente = forms.CharField(required=True, label="Número de Expediente")

    class Meta:
        model = Admision
        fields = ["num_expediente"]


class LegalesRectificarForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones"]
        widgets = {
            "observaciones": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Detalle sus observaciones.",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ProyectoDisposicionForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDisposicion
        exclude = [
            "admision",
            "creado",
            "creado_por",
            "archivo",
            "numero_if",
            "archivo_docx",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ProyectoConvenioForm(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        exclude = [
            "admision",
            "creado",
            "creado_por",
            "archivo",
            "numero_if",
            "archivo_docx",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class LegalesNumIFForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["legales_num_if"]
        labels = {
            "legales_num_if": "Número de expediente",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Precargar legales_num_if desde num_expediente si está vacío
        if (
            self.instance
            and self.instance.num_expediente
            and not self.instance.legales_num_if
        ):
            self.initial["legales_num_if"] = self.instance.num_expediente

        for field in self.fields.values():
            field.required = True

        # Hacer campo readonly para evitar errores de carga
        if self.instance and self.instance.num_expediente:
            self.fields["legales_num_if"].widget.attrs["readonly"] = True
            self.fields["legales_num_if"].help_text = (
                "Este número fue precargado desde el Informe Técnico"
            )


class DocumentosExpedienteForm(forms.ModelForm):
    class Meta:
        model = DocumentosExpediente
        fields = ["value", "tipo"]
        labels = {
            "value": "",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ConvenioNumIFFORM(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDeConvenio
        fields = ["numero_if"]
        labels = {
            "numero_if": "Número de IF de Proyecto de Convenio",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class DisposicionNumIFFORM(forms.ModelForm):
    class Meta:
        model = FormularioProyectoDisposicion
        fields = ["numero_if"]
        labels = {
            "numero_if": "Número de IF de Proyecto Disposición",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class IntervencionJuridicosForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = [
            "intervencion_juridicos",
            "rechazo_juridicos_motivo",
            "dictamen_motivo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["intervencion_juridicos"].required = True
        self.fields["rechazo_juridicos_motivo"].required = False
        self.fields["dictamen_motivo"].required = False

    def clean(self):
        cleaned_data = super().clean()
        intervencion = cleaned_data.get("intervencion_juridicos")
        motivo = cleaned_data.get("rechazo_juridicos_motivo")
        dictamen = cleaned_data.get("dictamen_motivo")

        if intervencion == "rechazado":
            if not motivo:
                self.add_error(
                    "rechazo_juridicos_motivo",
                    "Debe especificar el motivo cuando la intervención jurídica es Rechazado.",
                )
            elif motivo == "dictamen" and not dictamen:
                self.add_error(
                    "dictamen_motivo",
                    "Debe especificar el detalle cuando el motivo de rechazo es Dictamen.",
                )

        return cleaned_data


class InformeSGAForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["informe_sga"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ConvenioForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["numero_convenio", "archivo_convenio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class DisposicionForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["numero_disposicion", "archivo_disposicion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class IFInformeTecnicoForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["numero_if_tecnico"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class ReinicioExpedienteForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones_reinicio_expediente"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True


class SolicitarInformeComplementarioForm(forms.ModelForm):
    class Meta:
        model = Admision
        fields = ["observaciones_informe_tecnico_complementario"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
