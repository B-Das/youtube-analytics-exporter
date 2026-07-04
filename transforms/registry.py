import datetime

def minutes_to_hours(val):
    try:
        return round(float(val) / 60.0, 2)
    except Exception:
        return 0.0

def seconds_to_duration(val):
    try:
        total_seconds = int(float(val))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        return "00:00:00"

def round_2(val):
    try:
        return round(float(val), 2)
    except Exception:
        return 0.0

TRANSFORMS = {
    "minutes_to_hours": minutes_to_hours,
    "seconds_to_duration": seconds_to_duration,
    "round_2": round_2
}

def apply_transform(name: str, value):
    if not name or name not in TRANSFORMS:
        return value
    return TRANSFORMS[name](value)
