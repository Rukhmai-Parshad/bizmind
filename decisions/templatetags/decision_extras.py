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


@register.filter
def pair_with(labels, values):
    """[a, b] | pair_with:[1, 2]  ->  [(a, 1), (b, 2)] (for {% for label, value in ... %})."""
    return list(zip(labels, values))
