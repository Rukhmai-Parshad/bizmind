from django.db.models import Sum
from .models import FinanceRecord


def total_income(dataset):
    return (
        FinanceRecord.objects
        .filter(dataset=dataset, type='income')
        .aggregate(total=Sum('amount'))
        .get('total') or 0
    )


def total_expense(dataset):
    return (
        FinanceRecord.objects
        .filter(dataset=dataset, type='expense')
        .aggregate(total=Sum('amount'))
        .get('total') or 0
    )


def net_profit(dataset):
    return total_income(dataset) - total_expense(dataset)


def highest_expense_category(dataset):
    return (
        FinanceRecord.objects
        .filter(dataset=dataset, type='expense')
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('-total')
        .first()
    )
