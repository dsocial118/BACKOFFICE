from django import template

register = template.Library()


@register.filter
def entity_article(tipo_entidad_nombre):
    """Returns the appropriate article (LA/EL) for entity type"""
    if not tipo_entidad_nombre:
        return "EL/LA"

    nombre = tipo_entidad_nombre.lower()

    # Entities that use "LA"
    la_entities = [
        "asociación de hecho",
        "asociación civil",
        "cooperativa",
        "entidad",
        "fundación",
        "arquidiócesis",
        "diócesis",
        "parroquia",
    ]

    # Entities that use "EL"
    el_entities = ["obispado"]

    if nombre in la_entities:
        return "LA"
    elif nombre in el_entities:
        return "EL"
    else:
        return "EL/LA"


@register.filter
def get_item(dictionary, key):
    """Gets an item from a dictionary using a key"""
    if dictionary and key:
        return dictionary.get(key)
    return None


@register.filter
def split(value, delimiter):
    """Splits a string by delimiter"""
    return value.split(delimiter)


@register.inclusion_tag("admisiones/includes/boton_legales.html")
def render_boton_legales(boton, admision=None):
    """Renderiza un botón específico para el flujo de legales"""

    botones_config = {
        "rectificar": {
            "texto": "Rectificar",
            "modal": "#modalRectificar",
            "clase": "btn-warning",
        },
        "agregar_expediente": {
            "texto": "Agregar Número de expediente",
            "modal": "#modalLegalesNumIF",
            "clase": "btn-primary",
        },
        "formulario_convenio": {
            "texto": "Formulario Proyecto de Convenio",
            "modal": "#modalFormConvenio",
            "clase": "btn-primary",
        },
        "if_convenio": {
            "texto": "IF Proyecto de Convenio",
            "modal": "#modalConvenioNumIF",
            "clase": "btn-primary",
        },
        "formulario_disposicion": {
            "texto": "Formulario Proyecto Disposición",
            "modal": "#modalFormReso",
            "clase": "btn-primary",
        },
        "if_disposicion": {
            "texto": "IF Proyecto Disposición",
            "modal": "#modalDispoNumIF",
            "clase": "btn-primary",
        },
        "intervencion_juridicos": {
            "texto": "Intervención Jurídicos",
            "modal": "#modalIntervencionJuridicos",
            "clase": "btn-primary",
        },
        "informe_sga": {
            "texto": "Informe SGA",
            "modal": "#modalInformeSGA",
            "clase": "btn-primary",
        },
        "convenio": {
            "texto": "Convenio",
            "modal": "#modalConvenio",
            "clase": "btn-primary",
        },
        "disposicion": {
            "texto": "Disposición",
            "modal": "#modalDisposicion",
            "clase": "btn-primary",
        },
        "reinicio_expediente": {
            "texto": "Reinicio de Expediente",
            "modal": "#modalReinicioExpediente",
            "clase": "btn-danger",
        },
        "informe_complementario": {
            "texto": "Solicitar Informe Técnico Complementario",
            "modal": "#modalSolicitarInformeComplementario",
            "clase": "btn-primary",
        },
        "revisar_informe_complementario": {
            "texto": "Revisar Informe Complementario",
            "url": True,
            "clase": "btn-info",
        },
        "if_informe_complementario": {
            "texto": "IF Informe Técnico Complementario",
            "modal": "#modalIFInformeComplementario",
            "clase": "btn-primary",
        },
    }

    config = botones_config.get(boton, {})
    return {
        "texto": config.get("texto", ""),
        "modal": config.get("modal", ""),
        "clase": config.get("clase", "btn-primary"),
        "url": config.get("url", False),
        "admision": admision,
    }
