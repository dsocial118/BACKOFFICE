from django.contrib import admin
from acompanamientos.models.acompanamiento import InformacionRelevante
from acompanamientos.models.hitos import Hitos, HitosIntervenciones

# acompañamientos
admin.site.register(InformacionRelevante)

# hitos
admin.site.register(Hitos)
admin.site.register(HitosIntervenciones)
