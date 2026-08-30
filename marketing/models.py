from django.db import models
from datasets.models import Dataset
from django.utils import timezone


class MarketingRecord(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='marketing_records'
    )

    date = models.DateField()
    campaign = models.CharField(max_length=150)
    channel = models.CharField(max_length=100)

    impressions = models.PositiveIntegerField()
    clicks = models.PositiveIntegerField()
    conversions = models.PositiveIntegerField()

    spend = models.FloatField()
    revenue = models.FloatField()

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['dataset']),
            models.Index(fields=['date']),
            models.Index(fields=['channel']),
        ]

    def __str__(self):
        return f"{self.campaign} | {self.channel}"
