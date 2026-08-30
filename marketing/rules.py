from decisions.models import Decision
from marketing.queries import overall_ctr, overall_roas, worst_channel_by_roas
from decisions.confidence import clamp
from decisions.utils import DOMAIN_IMPACT, generate_insight_and_action


def low_ctr_rule(dataset, threshold=0.01):
    ctr = overall_ctr(dataset)
    if ctr >= threshold:
        return
    confidence = clamp((threshold - ctr) / threshold)
    insight, action = generate_insight_and_action("marketing", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="MARKETING_LOW_CTR",
        defaults={
            "domain": "marketing",
            "title": "Low Click-Through Rate Detected",
            "recommendation": "Optimize creatives and targeting strategy.",
            "explanation": f"CTR {ctr * 100:.2f}% is below the {threshold * 100:.2f}% benchmark.",
            "impact": DOMAIN_IMPACT["marketing"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence increases as CTR moves further below the benchmark.",
        },
    )


def poor_roas_rule(dataset, threshold=2.0):
    roas = overall_roas(dataset)
    if roas >= threshold:
        return
    confidence = clamp((threshold - roas) / threshold)
    insight, action = generate_insight_and_action("marketing", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="MARKETING_POOR_ROAS",
        defaults={
            "domain": "marketing", "title": "Poor Marketing ROI",
            "recommendation": "Reallocate budget to high-performing channels.",
            "explanation": f"ROAS {roas:.2f} is below the target of {threshold:.2f}.",
            "impact": DOMAIN_IMPACT["marketing"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence reflects the gap between actual ROAS and the target.",
        },
    )


def worst_channel_rule(dataset, relative_threshold=0.75):
    channel = worst_channel_by_roas(dataset)
    overall = overall_roas(dataset)
    if not channel or overall <= 0:
        return

    channel_roas = channel["revenue"] / channel["spend"]
    if channel_roas >= overall * relative_threshold:
        return

    confidence = clamp((overall - channel_roas) / overall)
    insight, action = generate_insight_and_action("marketing", confidence)
    Decision.objects.update_or_create(
        dataset=dataset, rule_name="MARKETING_WORST_CHANNEL",
        defaults={
            "domain": "marketing", "title": "Underperforming Marketing Channel",
            "recommendation": f"Review and consider reducing spend on {channel['channel']}.",
            "explanation": f"{channel['channel']} has ROAS {channel_roas:.2f}, at least 25% below the overall ROAS of {overall:.2f}.",
            "impact": DOMAIN_IMPACT["marketing"], "confidence": confidence,
            "insight": insight, "action": action,
            "confidence_reason": "Confidence reflects the channel's ROAS gap versus the overall campaign performance.",
        },
    )
