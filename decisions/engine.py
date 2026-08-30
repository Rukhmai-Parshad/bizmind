from django.db import transaction

from datasets.models import Dataset


def generate_decisions(dataset):
    """Generate domain-specific decisions exactly once for a dataset."""

    with transaction.atomic():
        locked_dataset = (
            Dataset.objects
            .select_for_update()
            .get(pk=dataset.pk)
        )

        if locked_dataset.decisions_generated:
            return

        if locked_dataset.type == "sales":
            from sales.rules import (
                region_focus_rule,
                revenue_health_check,
                top_product_rule,
            )

            rules = (
                revenue_health_check,
                region_focus_rule,
                top_product_rule,
            )

        elif locked_dataset.type == "marketing":
            from marketing.rules import (
                low_ctr_rule,
                poor_roas_rule,
                worst_channel_rule,
            )

            rules = (
                low_ctr_rule,
                poor_roas_rule,
                worst_channel_rule,
            )

        elif locked_dataset.type == "finance":
            from finance.rules import (
                high_expense_ratio_rule,
                net_loss_rule,
                top_expense_category_rule,
            )

            rules = (
                net_loss_rule,
                high_expense_ratio_rule,
                top_expense_category_rule,
            )

        else:
            raise ValueError(f"Unsupported dataset type: {locked_dataset.type}")

        for rule in rules:
            rule(locked_dataset)

        locked_dataset.decisions_generated = True
        locked_dataset.save(update_fields=("decisions_generated",))
