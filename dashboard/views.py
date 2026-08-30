from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render

from datasets.models import Dataset
from decisions.models import Decision


@login_required
def dashboard_home(request):
    user = request.user

    user_datasets = Dataset.objects.filter(uploaded_by=user)
    user_decisions = Decision.objects.filter(dataset__uploaded_by=user)

    total_datasets = user_datasets.count()
    processed_datasets = user_datasets.filter(is_processed=True).count()
    pending_datasets = user_datasets.filter(is_processed=False).count()
    total_decisions = user_decisions.count()

    confidence_counts = {
        "high": user_decisions.filter(confidence__gte=0.7).count(),
        "medium": user_decisions.filter(
            confidence__gte=0.4,
            confidence__lt=0.7,
        ).count(),
        "low": user_decisions.filter(confidence__lt=0.4).count(),
    }

    decisions_by_dataset = list(
        user_decisions
        .values("dataset__name")
        .annotate(count=Count("id"))
        .order_by("-count", "dataset__name")[:10]
    )

    decisions_by_domain = list(
        user_decisions
        .values("domain")
        .annotate(count=Count("id"))
        .order_by("-count", "domain")
    )

    context = {
        "total_datasets": total_datasets,
        "processed_datasets": processed_datasets,
        "pending_datasets": pending_datasets,
        "total_decisions": total_decisions,
        "has_decisions": total_decisions > 0,
        "recent_datasets": user_datasets.order_by("-uploaded_at")[:5],
        "recent_decisions": user_decisions.select_related("dataset").order_by("-created_at")[:5],
        "confidence_labels": ["High", "Medium", "Low"],
        "confidence_data": [
            confidence_counts["high"],
            confidence_counts["medium"],
            confidence_counts["low"],
        ],
        "dataset_labels": [item["dataset__name"] for item in decisions_by_dataset],
        "dataset_data": [item["count"] for item in decisions_by_dataset],
        "domain_labels": [item["domain"].title() for item in decisions_by_domain],
        "domain_data": [item["count"] for item in decisions_by_domain],
    }

    return render(request, "dashboard/home.html", context)
