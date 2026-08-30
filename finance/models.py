from django.db import models
from datasets.models import Dataset
from django.utils import timezone


class FinanceRecord(models.Model):
    TRANSACTION_TYPES = (
        ('income', 'Income'),
        ('expense', 'Expense'),
    )

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='finance_records'
    )

    date = models.DateField()
    category = models.CharField(max_length=100)
    department = models.CharField(max_length=100)

    amount = models.FloatField()
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['dataset']),
            models.Index(fields=['date']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.category} | {self.type} | {self.amount}"
