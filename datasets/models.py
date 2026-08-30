from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User


class Dataset(models.Model):
    DATASET_TYPES = (
        ("sales", "Sales"),
        ("marketing", "Marketing"),
        ("finance", "Finance"),
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="datasets",
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=DATASET_TYPES)
    file = models.FileField(upload_to="datasets/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    is_processed = models.BooleanField(default=False)
    decisions_generated = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    def clean(self):
        if not self.uploaded_by_id:
            return

        queryset = Dataset.objects.filter(
            uploaded_by=self.uploaded_by,
            name=self.name,
            type=self.type,
        )

        if self.pk:
            queryset = queryset.exclude(pk=self.pk)

        if queryset.exists():
            raise ValidationError(
                "You already uploaded a dataset with this name and type."
            )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("uploaded_by", "name", "type"),
                name="unique_dataset_per_user",
            )
        ]
        ordering = ("-uploaded_at",)

    def __str__(self):
        return f"{self.name} ({self.type})"
