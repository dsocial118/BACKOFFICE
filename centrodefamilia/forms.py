from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from ciudadanos.models import Sexo, TipoDocumento
from organizaciones.models import Organizacion
from centrodefamilia.models import (
    Centro,
    ActividadCentro,
    ParticipanteActividad,
    Categoria,
    Actividad,
    Expediente,
)

HORAS_DEL_DIA = [(f"{h:02d}:00", f"{h:02d}:00") for h in range(0, 24)] + [
    (f"{h:02d}:30", f"{h:02d}:30") for h in range(0, 24)
]


class CentroForm(forms.ModelForm):
    class Meta:
        model = Centro
        fields = [
            "tipo",
            "nombre",
            "codigo",
            "organizacion_asociada",
            "domicilio_actividad",
            "telefono",
            "celular",
            "correo",
            "sitio_web",
            "link_redes",
            "nombre_referente",
            "apellido_referente",
            "telefono_referente",
            "correo_referente",
            "referente",
            "faro_asociado",
            "foto",
            "activo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optimización: Cargar solo usuarios ReferenteCentro con select_related
        self.fields["referente"].queryset = User.objects.filter(
            groups__name="ReferenteCentro"
        ).only("id", "username", "first_name", "last_name")

        # Optimización: Cargar solo centros faro activos
        self.fields["faro_asociado"].queryset = Centro.objects.filter(
            tipo="faro", activo=True
        ).only("id", "nombre")

        # Optimización: Usar empty_label y limitar queryset para organizaciones
        # Solo cargar las primeras 100 organizaciones para evitar query lenta
        self.fields["organizacion_asociada"].queryset = Organizacion.objects.only(
            "id", "nombre", "cuit"
        )[
            :100
        ]  # Limitar a las primeras 100
        self.fields["organizacion_asociada"].empty_label = "Seleccionar organización..."

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        faro_asociado = cleaned_data.get("faro_asociado")

        if tipo == "adherido" and not faro_asociado:
            raise ValidationError(
                "Debe asociar un Centro FARO activo si el centro es ADHERIDO."
            )
        if tipo == "faro" and faro_asociado:
            raise ValidationError("Un Centro FARO no puede tener un FARO asociado.")
        return cleaned_data


class ActividadCentroForm(forms.ModelForm):
    dias = forms.SelectMultiple(
        attrs={
            "class": "form-select select2 w-100",
            "style": "width: 100%;",
        }
    )
    horarios = forms.TimeField(
        label="Hora",
        widget=forms.TimeInput(
            attrs={
                "class": "form-control timepicker",
                "placeholder": "Seleccione una hora",
            }
        ),
        required=True,
    )
    categoria = forms.ModelChoiceField(
        queryset=Categoria.objects.all(),
        required=False,
        label="Categoría",
        empty_label="Seleccione una categoría",
    )

    class Meta:
        model = ActividadCentro
        fields = [
            "categoria",
            "actividad",
            "cantidad_personas",
            "dias",
            "horarios",
            "precio",
            "estado",
        ]
        exclude = ["centro"]
        widgets = {
            "horarios": forms.TextInput(attrs={"class": "form-control"}),
            "cantidad_personas": forms.NumberInput(attrs={"class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control"}),
            "estado": forms.Select(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        self.centro = kwargs.pop("centro", None)
        super().__init__(*args, **kwargs)

        # Si se pasó un dato de categoría, filtramos las actividades
        if "data" in kwargs:
            categoria_id = kwargs["data"].get("categoria")
            if categoria_id:
                self.fields["actividad"].queryset = Actividad.objects.filter(
                    categoria_id=categoria_id
                )
            else:
                self.fields["actividad"].queryset = Actividad.objects.none()
        else:
            self.fields["actividad"].queryset = Actividad.objects.none()

        # Si es FARO, ocultar el campo precio
        if self.centro and self.centro.tipo == "faro":
            self.fields["precio"].widget = forms.HiddenInput()
            self.fields["precio"].required = False

    def clean(self):
        cleaned_data = super().clean()
        precio = cleaned_data.get("precio")

        if self.centro and self.centro.tipo == "faro" and precio:
            raise ValidationError(
                "Un centro de tipo FARO no debe tener un precio asignado."
            )
        return cleaned_data


class ParticipanteActividadForm(forms.ModelForm):
    nombre = forms.CharField(max_length=255, label="Nombre")
    apellido = forms.CharField(max_length=255, label="Apellido")
    fecha_nacimiento = forms.DateField(
        label="Fecha de Nacimiento", widget=forms.DateInput(attrs={"type": "date"})
    )
    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.all(), label="Tipo de Documento"
    )
    dni = forms.IntegerField(label="Documento")
    genero = forms.ModelChoiceField(queryset=Sexo.objects.all(), label="Sexo")

    class Meta:
        model = ParticipanteActividad
        fields = (
            []
        )  # no usamos directamente los campos del modelo porque todos se construyen en la vista


class ExpedienteCabalForm(forms.ModelForm):
    class Meta:
        model = Expediente
        fields = [
            "archivo",
            "periodo",
        ]
        widgets = {
            "archivo": forms.FileInput(attrs={"class": "form-control"}),
            "periodo": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class ActividadForm(forms.ModelForm):
    class Meta:
        model = Actividad
        fields = [
            "nombre",
            "categoria",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
        }
