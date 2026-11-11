"""Comfort index and rule-based recommendations (no external AI service needed)."""
import math

# (field, ideal range, penalty threshold)
_METRICS = [
    ("temperature", (20, 24), 5),
    ("humidity", (30, 60), 30),
    ("gas", (400, 1000), 1000),
    ("light", (300, 1000), 500),
    ("sound", (0, 50), 40),
]

_TIPS = {
    ("temperature", "low"): ("Increase the heating or close the windows.", "The room is colder than the comfortable 20–24 °C range."),
    ("temperature", "high"): ("Cool the room: open a window or reduce heating.", "The room is warmer than the comfortable 20–24 °C range."),
    ("humidity", "low"): ("Increase air humidity (humidifier, ventilate after rain).", "Air is drier than the comfortable 30–60 % range."),
    ("humidity", "high"): ("Ventilate the room to reduce humidity.", "Air is more humid than the comfortable 30–60 % range."),
    ("gas", "low"): ("Check the air quality sensor.", "Reading is below the normal indoor level (400 ppm)."),
    ("gas", "high"): ("Ventilate the room: open windows or doors.", "CO₂ is above 1000 ppm, which reduces concentration."),
    ("light", "low"): ("Turn on more lights or open the blinds.", "Illumination is below the recommended 300 lx."),
    ("light", "high"): ("Reduce glare: use blinds or dim the lights.", "Illumination is above the recommended 1000 lx."),
    ("sound", "high"): ("Reduce noise: close the door and ask for quiet.", "Noise is above the recommended 50 dB."),
}


def calculate_manual_comfort(latest: dict) -> int:
    total = 0.0
    for field, (lo, hi), threshold in _METRICS:
        val = latest[field]
        score = 1.0
        if val < lo:
            score = 1 - (lo - val) / threshold
        elif val > hi:
            score = 1 - (val - hi) / threshold
        total += max(0.0, min(1.0, score))
    return math.floor(total / len(_METRICS) * 100 + 0.5)  # like Math.round


def generate_tips(latest: dict) -> list[dict]:
    """Rule-based tips for metrics outside their ideal range, most severe first."""
    found = []
    for field, (lo, hi), threshold in _METRICS:
        val = latest[field]
        if val < lo:
            side, severity = "low", (lo - val) / threshold
        elif val > hi:
            side, severity = "high", (val - hi) / threshold
        else:
            continue
        if (field, side) not in _TIPS:
            continue
        message, reason = _TIPS[(field, side)]
        priority = "high" if severity >= 0.6 else "medium" if severity >= 0.25 else "low"
        found.append((severity, {"priority": priority, "type": field, "message": message, "reason": reason}))
    found.sort(key=lambda x: x[0], reverse=True)
    return [{"id": i + 1, **tip} for i, (_, tip) in enumerate(found)]
