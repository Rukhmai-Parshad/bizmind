from django.test import TestCase

from accounts.models import User
from datasets.models import Dataset
from .models import Decision


class DecisionModelTests(TestCase):
    def test_confidence_is_stored_for_a_decision(self):
        user = User.objects.create_user(
            email="user@example.com",
            password="strong-password-123",
        )
        dataset = Dataset.objects.create(
            uploaded_by=user,
            name="Sales Test",
            type="sales",
            file="datasets/test.csv",
        )
        decision = Decision.objects.create(
            dataset=dataset,
            title="Revenue Risk",
            rule_name="SALES_REVENUE_HEALTH",
            domain="sales",
            recommendation="Review pricing.",
            explanation="Revenue is below threshold.",
            confidence=0.8,
        )

        self.assertEqual(decision.confidence, 0.8)
