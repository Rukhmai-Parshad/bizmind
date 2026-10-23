import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import DatasetUploadForm
from .models import Dataset
from .services import save_and_process_dataset
from .validators import can_upload

logger = logging.getLogger(__name__)


@login_required
def dataset_list(request):
    datasets = Dataset.objects.filter(
        uploaded_by=request.user
    ).order_by("-uploaded_at")

    return render(
        request,
        "datasets/dataset_list.html",
        {"datasets": datasets},
    )


@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(
        Dataset,
        pk=pk,
        uploaded_by=request.user,
    )

    decisions = dataset.decisions.all()

    return render(
        request,
        "datasets/dataset_detail.html",
        {
            "dataset": dataset,
            "decisions": decisions,
        },
    )


@login_required
def upload_dataset(request):
    if not can_upload(request.user):
        messages.error(request, "Your account has read-only access.")
        return redirect("dashboard:home")

    if request.method == "POST":
        form = DatasetUploadForm(request.POST, request.FILES, user=request.user)

        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.uploaded_by = request.user

            try:
                # All or nothing: on any failure the row, records and file are gone.
                save_and_process_dataset(dataset)

            except ValueError as exc:
                logger.warning("Dataset validation failed (type=%s, user_id=%s): %s", dataset.type, request.user.pk, exc)
                messages.error(request, f"Dataset could not be processed: {exc}")
            except Exception:
                logger.exception("Dataset processing failed (type=%s, user_id=%s)", dataset.type, request.user.pk)
                messages.error(
                    request,
                    "The dataset could not be processed because of an unexpected error. "
                    "Please try again or contact support.",
                )
            else:
                messages.success(
                    request,
                    "Dataset uploaded and processed successfully.",
                )
                return redirect("datasets:dataset_list")
    else:
        form = DatasetUploadForm(user=request.user)

    return render(request, "datasets/upload.html", {"form": form})
