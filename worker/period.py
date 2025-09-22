def assign_period(hour):
    """Gán buổi trong ngày dựa trên giờ"""
    if hour in [0, 3]:
        return "Early Morning"
    elif hour in [6, 9]:
        return "Morning"
    elif hour in [12]:
        return "Noon"
    elif hour in [15, 18]:
        return "Afternoon"
    elif hour in [21]:
        return "Evening"
    else:
        return None


def assign_period_uv(hour):
    """Gán buổi trong ngày dựa trên giờ"""
    if 0 <= hour <= 5:
        return "Early Morning"
    elif 6 <= hour <= 9:
        return "Morning"
    elif 10 <= hour <= 12:
        return "Noon"
    elif 13 <= hour <= 18:
        return "Afternoon"
    elif 19 <= hour <= 23:
        return "Evening"
    else:
        return None