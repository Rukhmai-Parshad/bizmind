from django.db.models import Sum
from .models import MarketingRecord


def total_spend(dataset):
    return MarketingRecord.objects.filter(dataset=dataset).aggregate(total=Sum("spend")).get("total") or 0


def total_revenue(dataset):
    return MarketingRecord.objects.filter(dataset=dataset).aggregate(total=Sum("revenue")).get("total") or 0


def overall_ctr(dataset):
    agg = MarketingRecord.objects.filter(dataset=dataset).aggregate(
        clicks=Sum("clicks"), impressions=Sum("impressions")
    )
    if not agg["impressions"]:
        return 0
    return agg["clicks"] / agg["impressions"]


def overall_roas(dataset):
    spend = total_spend(dataset)
    revenue = total_revenue(dataset)
    if spend == 0:
        return 0
    return revenue / spend


def worst_channel_by_roas(dataset):
    qs = (
        MarketingRecord.objects.filter(dataset=dataset)
        .values("channel")
        .annotate(spend=Sum("spend"), revenue=Sum("revenue"))
        .exclude(spend=0)
    )
    return min(qs, key=lambda row: row["revenue"] / row["spend"], default=None)
