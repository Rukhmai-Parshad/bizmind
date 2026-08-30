def clamp(value, min_val=0.0, max_val=1.0):
    return max(min(value, max_val), min_val)


def linear_confidence(distance, max_distance):
    """
    distance: how far metric is from safe zone
    max_distance: worst acceptable distance
    """
    if max_distance <= 0:
        return 0.0

    score = distance / max_distance
    return clamp(score)
