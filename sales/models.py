from django.db import models
from datasets.models import Dataset
from django.utils import timezone


class SalesRecord(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='sales_records'
    )

    date = models.DateField()
    product = models.CharField(max_length=100)
    region = models.CharField(max_length=100)

    units_sold = models.PositiveIntegerField()
    unit_price = models.FloatField()
    revenue = models.FloatField(editable=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['dataset']),
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"{self.product} | {self.region}"
