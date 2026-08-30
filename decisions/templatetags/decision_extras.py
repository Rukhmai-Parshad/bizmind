from django import template

register = template.Library()


@register.filter
def confidence_label(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Unknown"

    if value >= 0.7:
        return "High Confidence"
    elif value >= 0.4:
        return "Medium Confidence"
    return "Low Confidence"


@register.filter
def confidence_badge(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "badge-secondary"

    if value >= 0.7:
        return "badge-success"
    elif value >= 0.4:
        return "badge-warning"
    return "badge-danger"
