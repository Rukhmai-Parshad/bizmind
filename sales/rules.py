from sales.queries import total_revenue, worst_region, top_product
from decisions.confidence import clamp, linear_confidence
from decisions.models import Decision
from decisions.utils import DOMAIN_IMPACT, generate_insight_and_action


def revenue_health_check(dataset, threshold=10000):
    revenue = total_revenue(dataset)
    if revenue >= threshold:
        return

    confidence = linear_confidence(threshold - revenue, threshold)
    insight, action = generate_insight_and_action("sales", confidence)

    Decision.objects.update_or_create(
        dataset=dataset,
        rule_name="SALES_REVENUE_HEALTH",
        defaults={
            "domain": "sales",
            "title": "Revenue Risk Detected",
            "recommendation": "Improve pricing and focus on high-margin products.",
            "explanation": f"Revenue {revenue:.2f} is below the benchmark of {threshold:.2f}.",
            "impact": DOMAIN_IMPACT["sales"],
            "confidence": confidence,
            "insight": insight,
            "action": action,
            "confidence_reason": "Confidence increases as revenue moves further below the benchmark.",
        },
    )


def region_focus_rule(dataset, threshold=0.20):
    region = worst_region(dataset)
    total = total_revenue(dataset)
    if not region or total <= 0:
        return

    ratio = region["total_revenue"] / total
    if ratio >= threshold:
        return

    confidence = clamp((threshold - ratio) / threshold)
    insight, action = generate_insight_and_action("sales", confidence)

    Decision.objects.update_or_create(
        dataset=dataset,
        rule_name="SALES_REGION_FOCUS",
        defaults={
            "domain": "sales",
            "title": "Underperforming Sales Region",
            "recommendation": f"Investigate performance in {region['region']}.",
            "explanation": f"{region['region']} contributes only {ratio * 100:.2f}% of total revenue, below the {threshold * 100:.0f}% benchmark.",
            "impact": DOMAIN_IMPACT["sales"],
            "confidence": confidence,
            "insight": insight,
            "action": action,
            "confidence_reason": "Confidence is based on how far the region's revenue share falls below the benchmark.",
        },
    )


def top_product_rule(dataset, threshold=0.40):
    product = top_product(dataset)
    total = total_revenue(dataset)
    if not product or total <= 0:
        return

    dominance = product["total_revenue"] / total
    if dominance < threshold:
        return

    confidence = clamp(dominance)
    insight, action = generate_insight_and_action("sales", confidence)

    Decision.objects.update_or_create(
        dataset=dataset,
        rule_name="SALES_TOP_PRODUCT",
        defaults={
            "domain": "sales",
            "title": "Top Performing Product",
            "recommendation": f"Prioritize and scale sales of {product['product']}.",
            "explanation": f"{product['product']} contributes {dominance * 100:.2f}% of total revenue, indicating strong concentration.",
            "impact": DOMAIN_IMPACT["sales"],
            "confidence": confidence,
            "insight": insight,
            "action": action,
            "confidence_reason": "Confidence reflects the product's share of total revenue.",
        },
    )
