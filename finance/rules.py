from decisions.models import Decision
from finance.queries import total_income, total_expense, net_profit, highest_expense_category
from decisions.confidence import clamp
from decisions.utils import DOMAIN_IMPACT, generate_insight_and_action


def net_loss_rule(dataset):
    profit = net_profit(dataset)
    if profit >= 0:
        return
    loss = abs(profit)
    income = total_income(dataset)
    confidence = clamp(loss / income) if income else 1.0
    insight, action = generate_insight_and_action("finance", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="FINANCE_NET_LOSS",
        defaults={
            "domain": "finance", "title": "Company Operating at a Loss",
            "recommendation": "Cut non-essential expenses and review cost drivers.",
            "explanation": f"Net loss detected: {loss:.2f}.",
            "impact": DOMAIN_IMPACT["finance"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence reflects the loss relative to total income.",
        },
    )


def high_expense_ratio_rule(dataset, threshold=0.80):
    income = total_income(dataset)
    expense = total_expense(dataset)
    if income <= 0:
        return
    ratio = expense / income
    if ratio < threshold:
        return
    confidence = clamp((ratio - threshold) / max(1 - threshold, 0.01))
    insight, action = generate_insight_and_action("finance", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="FINANCE_HIGH_EXPENSE_RATIO",
        defaults={
            "domain": "finance", "title": "High Expense-to-Income Ratio",
            "recommendation": "Review recurring and discretionary expenses.",
            "explanation": f"Expenses are {ratio * 100:.2f}% of income.",
            "impact": DOMAIN_IMPACT["finance"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence reflects how far the expense ratio exceeds the benchmark.",
        },
    )


def top_expense_category_rule(dataset, threshold=0.40):
    category = highest_expense_category(dataset)
    total_expense_value = total_expense(dataset)
    if not category or total_expense_value <= 0:
        return

    share = category["total"] / total_expense_value
    if share < threshold:
        return

    confidence = clamp(share)
    insight, action = generate_insight_and_action("finance", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="FINANCE_TOP_EXPENSE_CATEGORY",
        defaults={
            "domain": "finance", "title": "Significant Expense Category Identified",
            "recommendation": f"Review spending in {category['category']}.",
            "explanation": f"{category['category']} accounts for {share * 100:.2f}% of total expenses.",
            "impact": DOMAIN_IMPACT["finance"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence reflects the category's share of total expenses.",
        },
    )
