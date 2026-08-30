from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from datasets.models import Dataset
from .models import Decision

@login_required
def dataset_decisions(request, dataset_id):
    dataset = get_object_or_404(
        Dataset,
        id=dataset_id,
        uploaded_by=request.user
    )

    decisions = dataset.decisions.all().select_related("dataset")

    return render(request, 'decisions/list.html', {
        'dataset': dataset,
        'decisions': decisions
    })

@login_required
def filtered_decisions(request):
    domain = request.GET.get("domain")
    confidence = request.GET.get("confidence")

    qs = Decision.objects.filter(
        dataset__uploaded_by=request.user
    ).select_related("dataset")

    VALID_DOMAINS = ["sales", "marketing", "finance"]

    if domain in VALID_DOMAINS:
        qs = qs.filter(domain=domain)

    if confidence == "high":
        qs = qs.filter(confidence__gte=0.7)
    elif confidence == "medium":
        qs = qs.filter(confidence__gte=0.4, confidence__lt=0.7)
    elif confidence == "low":
        qs = qs.filter(confidence__lt=0.4)

    return render(
        request,
        "decisions/filtered_list.html",
        {
            "decisions": qs,
            "selected_domain": domain,
            "selected_confidence": confidence,
        }
    )
