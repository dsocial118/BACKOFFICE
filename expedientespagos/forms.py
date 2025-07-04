from django import forms
from expedientespagos.models import ExpedientePago


class ExpedientePagoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = ExpedientePago
        fields = "__all__"
        exclude = ["comedor"]
        widgets = {
            "usuario": forms.Select(attrs={"class": "form-control"}),
            "fecha_pago_al_banco": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "fecha_acreditacion": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
        }
        labels = {
            "nombre": "Nombre del Expediente",
            "usuario": "Usuario Responsable",
            "estado": "Estado del Expediente",
        }
