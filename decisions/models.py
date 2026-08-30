from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from datasets.models import Dataset


class Decision(models.Model):
    DOMAIN_CHOICES = (
        ('sales', 'Sales'),
        ('marketing', 'Marketing'),
        ('finance', 'Finance'),
    )

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='decisions'
    )

    title = models.CharField(max_length=255)
    rule_name = models.CharField(max_length=100, db_index=True)

    domain = models.CharField(
        max_length=20,
        choices=DOMAIN_CHOICES,
        db_index=True
    )

    insight = models.CharField(
        max_length=255,
        default="Data shows a meaningful business pattern."
    )

    recommendation = models.TextField()
    explanation = models.TextField()

    action = models.CharField(
        max_length=255,
        default="Recommended to take strategic action."
    )

    impact = models.CharField(
    max_length=255,
    blank=True
    )


    confidence = models.FloatField(
        help_text="Value between 0 and 1",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )

    confidence_reason = models.CharField(
    max_length=255,
    default="Derived from deviation against expected benchmarks."
    )


    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['dataset', 'domain', 'rule_name'],
                name='unique_decision_per_dataset_domain_rule'
            )
        ]
        indexes = [
            models.Index(fields=['dataset', 'domain']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.dataset.name} | {self.domain} | {self.rule_name}"
