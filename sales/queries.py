from django.db.models import Sum
from .models import SalesRecord


def total_revenue(dataset):
    """
    Returns total revenue for a given dataset.
    Always returns a number (never None).
    """
    return (
        SalesRecord.objects
        .filter(dataset=dataset)
        .aggregate(total=Sum('revenue'))
        .get('total')
        or 0
    )


def top_product(dataset):
    """
    Returns top product by revenue.
    Example:
    {'product': 'Product A', 'total_revenue': 15000}
    """
    return (
        SalesRecord.objects
        .filter(dataset=dataset)
        .values('product')
        .annotate(total_revenue=Sum('revenue'))
        .order_by('-total_revenue')
        .first()
    )


def worst_region(dataset):
    """
    Returns lowest performing region.
    Example:
    {'region': 'West', 'total_revenue': 3200}
    """
    return (
        SalesRecord.objects
        .filter(dataset=dataset)
        .values('region')
        .annotate(total_revenue=Sum('revenue'))
        .order_by('total_revenue')
        .first()
    )


def daily_sales_trend(dataset):
    """
    Date-wise revenue trend.
    """
    return (
        SalesRecord.objects
        .filter(dataset=dataset)
        .values('date')
        .annotate(total_revenue=Sum('revenue'))
        .order_by('date')
    )
