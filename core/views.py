from django.contrib.auth import get_user_model
from django.db.models import Count
from django.shortcuts import render

from datasets.models import Dataset
from decisions.models import Decision


def home(request):
    return render(request, "core/home.html")


def about(request):
    return render(request, "core/about.html")


def stats(request):
    total_users = get_user_model().objects.filter(is_active=True).count()
    total_datasets = Dataset.objects.filter(is_processed=True).count()
    total_decisions = Decision.objects.count()

    confidence = {
        "high": Decision.objects.filter(confidence__gte=0.7).count(),
        "medium": Decision.objects.filter(
            confidence__gte=0.4,
            confidence__lt=0.7,
        ).count(),
        "low": Decision.objects.filter(confidence__lt=0.4).count(),
    }

    domain_usage = list(
        Decision.objects
        .values("domain")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    return render(
        request,
        "core/stats.html",
        {
            "total_users": total_users,
            "total_datasets": total_datasets,
            "total_decisions": total_decisions,
            "confidence_high": confidence["high"],
            "confidence_medium": confidence["medium"],
            "confidence_low": confidence["low"],
            "domain_usage": domain_usage,
        },
    )


def contact(request):
    return render(request, "core/contact.html")
