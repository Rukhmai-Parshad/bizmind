# decisions/utils.py

DOMAIN_IMPACT = {
    "sales": "Revenue and growth risk if ignored.",
    "marketing": "Marketing spend inefficiency and low ROI risk.",
    "finance": "Profitability and cash flow risk.",
}


def generate_insight_and_action(domain, confidence):
    """
    Generates insight & action text based on domain + confidence
    """

    if confidence >= 0.8:
        insight = "Strong data signals indicate a critical business issue."
        action = "Immediate action recommended to minimize risk."

    elif confidence >= 0.5:
        insight = "Moderate signals detected; trend is emerging."
        action = "Monitor closely and prepare corrective actions."

    else:
        insight = "Weak signals detected; data patterns are unstable."
        action = "Collect more data before taking major action."

    return insight, action
