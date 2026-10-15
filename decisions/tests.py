from datetime import date

from django.test import TestCase

from accounts.models import User
from datasets.models import Dataset
from finance.models import FinanceRecord
from finance.rules import high_expense_ratio_rule, net_loss_rule, top_expense_category_rule
from marketing.models import MarketingRecord
from marketing.rules import low_ctr_rule, poor_roas_rule, worst_channel_rule
from sales.models import SalesRecord
from sales.rules import region_focus_rule, revenue_health_check, top_product_rule

from .engine import generate_decisions
from .models import Decision

PASSWORD = "strong-password-123"


class DecisionModelTests(TestCase):
    def test_confidence_is_stored_for_a_decision(self):
        user = User.objects.create_user(
            email="user@example.com",
            password=PASSWORD,
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


class DecisionRuleCharacterisationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="rules@example.com",
            password=PASSWORD,
            role="ANALYST",
        )

    def _dataset(self, name, dataset_type):
        return Dataset.objects.create(
            uploaded_by=self.user,
            name=name,
            type=dataset_type,
            file=f"datasets/{name}.csv",
        )

    def _sale(self, dataset, product, region, units_sold, unit_price):
        SalesRecord.objects.create(
            dataset=dataset,
            date=date(2024, 1, 1),
            product=product,
            region=region,
            units_sold=units_sold,
            unit_price=unit_price,
            revenue=units_sold * unit_price,
        )

    def _marketing(self, dataset, channel, impressions, clicks, conversions, spend, revenue):
        MarketingRecord.objects.create(
            dataset=dataset,
            date=date(2024, 1, 1),
            campaign="Spring",
            channel=channel,
            impressions=impressions,
            clicks=clicks,
            conversions=conversions,
            spend=spend,
            revenue=revenue,
        )

    def _finance(self, dataset, category, amount, record_type, department="Ops"):
        FinanceRecord.objects.create(
            dataset=dataset,
            date=date(2024, 1, 1),
            category=category,
            department=department,
            amount=amount,
            type=record_type,
        )

    def test_sales_revenue_health_fires_below_10000(self):
        dataset = self._dataset("rev-low", "sales")
        self._sale(dataset, "Widget", "North", 10, 100)
        revenue_health_check(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_REVENUE_HEALTH").exists()
        )

    def test_sales_revenue_health_does_not_fire_at_10000(self):
        dataset = self._dataset("rev-ok", "sales")
        self._sale(dataset, "Widget", "North", 100, 100)
        revenue_health_check(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_REVENUE_HEALTH").exists()
        )

    def test_sales_region_focus_fires_when_share_below_20_percent(self):
        dataset = self._dataset("region-low", "sales")
        self._sale(dataset, "Widget", "North", 90, 100)
        self._sale(dataset, "Widget", "South", 5, 100)
        region_focus_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_REGION_FOCUS").exists()
        )

    def test_sales_region_focus_does_not_fire_when_share_is_at_least_20_percent(self):
        dataset = self._dataset("region-ok", "sales")
        self._sale(dataset, "Widget", "North", 50, 100)
        self._sale(dataset, "Widget", "South", 50, 100)
        region_focus_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_REGION_FOCUS").exists()
        )

    def test_sales_top_product_fires_at_40_percent_share(self):
        dataset = self._dataset("product-high", "sales")
        self._sale(dataset, "Alpha", "North", 40, 100)
        self._sale(dataset, "Beta", "North", 30, 100)
        self._sale(dataset, "Gamma", "North", 30, 100)
        top_product_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_TOP_PRODUCT").exists()
        )

    def test_sales_top_product_does_not_fire_below_40_percent_share(self):
        dataset = self._dataset("product-even", "sales")
        self._sale(dataset, "Alpha", "North", 30, 100)
        self._sale(dataset, "Beta", "North", 30, 100)
        self._sale(dataset, "Gamma", "North", 30, 100)
        top_product_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="SALES_TOP_PRODUCT").exists()
        )

    def test_marketing_low_ctr_fires_below_1_percent(self):
        dataset = self._dataset("ctr-low", "marketing")
        self._marketing(dataset, "Search", 10000, 50, 5, 100, 200)
        low_ctr_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_LOW_CTR").exists()
        )

    def test_marketing_low_ctr_does_not_fire_at_1_percent(self):
        dataset = self._dataset("ctr-ok", "marketing")
        self._marketing(dataset, "Search", 10000, 100, 5, 100, 200)
        low_ctr_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_LOW_CTR").exists()
        )

    def test_marketing_poor_roas_fires_below_2(self):
        dataset = self._dataset("roas-low", "marketing")
        self._marketing(dataset, "Search", 1000, 50, 5, 100, 100)
        poor_roas_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_POOR_ROAS").exists()
        )

    def test_marketing_poor_roas_does_not_fire_at_2(self):
        dataset = self._dataset("roas-ok", "marketing")
        self._marketing(dataset, "Search", 1000, 50, 5, 100, 200)
        poor_roas_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_POOR_ROAS").exists()
        )

    def test_marketing_worst_channel_fires_when_roas_is_25_percent_below_overall(self):
        dataset = self._dataset("channel-low", "marketing")
        self._marketing(dataset, "Search", 1000, 50, 5, 100, 300)
        self._marketing(dataset, "Social", 1000, 50, 5, 100, 100)
        worst_channel_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_WORST_CHANNEL").exists()
        )

    def test_marketing_worst_channel_does_not_fire_when_channels_are_close(self):
        dataset = self._dataset("channel-ok", "marketing")
        self._marketing(dataset, "Search", 1000, 50, 5, 100, 200)
        self._marketing(dataset, "Social", 1000, 50, 5, 100, 200)
        worst_channel_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="MARKETING_WORST_CHANNEL").exists()
        )

    def test_finance_net_loss_fires_when_expenses_exceed_income(self):
        dataset = self._dataset("loss", "finance")
        self._finance(dataset, "Sales", 100, "income")
        self._finance(dataset, "Rent", 200, "expense")
        net_loss_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(dataset=dataset, rule_name="FINANCE_NET_LOSS").exists()
        )

    def test_finance_net_loss_does_not_fire_when_profitable(self):
        dataset = self._dataset("profit", "finance")
        self._finance(dataset, "Sales", 200, "income")
        self._finance(dataset, "Rent", 100, "expense")
        net_loss_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(dataset=dataset, rule_name="FINANCE_NET_LOSS").exists()
        )

    def test_finance_high_expense_ratio_fires_at_80_percent(self):
        dataset = self._dataset("expense-high", "finance")
        self._finance(dataset, "Sales", 100, "income")
        self._finance(dataset, "Rent", 80, "expense")
        high_expense_ratio_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(
                dataset=dataset, rule_name="FINANCE_HIGH_EXPENSE_RATIO"
            ).exists()
        )

    def test_finance_high_expense_ratio_does_not_fire_below_80_percent(self):
        dataset = self._dataset("expense-ok", "finance")
        self._finance(dataset, "Sales", 100, "income")
        self._finance(dataset, "Rent", 70, "expense")
        high_expense_ratio_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(
                dataset=dataset, rule_name="FINANCE_HIGH_EXPENSE_RATIO"
            ).exists()
        )

    def test_finance_top_expense_category_fires_at_40_percent_share(self):
        dataset = self._dataset("category-high", "finance")
        self._finance(dataset, "Rent", 40, "expense")
        self._finance(dataset, "Payroll", 30, "expense")
        self._finance(dataset, "Travel", 30, "expense")
        top_expense_category_rule(dataset)
        self.assertTrue(
            Decision.objects.filter(
                dataset=dataset, rule_name="FINANCE_TOP_EXPENSE_CATEGORY"
            ).exists()
        )

    def test_finance_top_expense_category_does_not_fire_below_40_percent_share(self):
        dataset = self._dataset("category-even", "finance")
        self._finance(dataset, "Rent", 30, "expense")
        self._finance(dataset, "Payroll", 30, "expense")
        self._finance(dataset, "Travel", 30, "expense")
        top_expense_category_rule(dataset)
        self.assertFalse(
            Decision.objects.filter(
                dataset=dataset, rule_name="FINANCE_TOP_EXPENSE_CATEGORY"
            ).exists()
        )

    def test_generate_decisions_runs_sales_rules_once(self):
        dataset = self._dataset("engine-sales", "sales")
        self._sale(dataset, "Widget", "North", 2, 100)
        generate_decisions(dataset)
        first_count = Decision.objects.filter(dataset=dataset).count()
        generate_decisions(dataset)
        self.assertEqual(Decision.objects.filter(dataset=dataset).count(), first_count)
        dataset.refresh_from_db()
        self.assertTrue(dataset.decisions_generated)
        self.assertGreaterEqual(first_count, 1)
        self.assertLessEqual(first_count, 3)
