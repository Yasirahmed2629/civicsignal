import numpy as np
from sklearn.cluster import DBSCAN
from collections import Counter

EARTH_RADIUS_KM = 6371.0088

CLUSTER_RADIUS_KM = 0.5
MIN_REQUESTS_PER_HOTSPOT = 2

URGENCY_RANK = {"low": 0, "medium": 1, "high": 2}

CATEGORY_WEIGHT = {
    "safety": 1.0,
    "healthcare": 1.0,
    "water": 0.8,
    "electricity": 0.7,
    "sanitation": 0.6,
    "roads": 0.5,
    "education": 0.4,
    "general": 0.2,
}

# --- Demographic / infrastructure data fusion ---
# Static demo dataset combining population density and existing
# infrastructure quality per area. In production this would come from
# census / national infrastructure index data sources. Score is 0-1:
# higher = more people affected AND/OR weaker existing infrastructure,
# meaning citizen reports here deserve more weight.
#
# population_density: relative density band for the area (low/medium/high)
# infra_score: existing infrastructure quality, 0 (very poor) to 1 (excellent)
#              — LOWER infra_score means MORE need, so we invert it in scoring.
AREA_DEMOGRAPHICS = {
    "koramangala":       {"population_density": "high",   "infra_score": 0.7},
    "mg road":           {"population_density": "high",   "infra_score": 0.8},
    "central market":    {"population_density": "high",   "infra_score": 0.4},
    "connaught place":   {"population_density": "high",   "infra_score": 0.6},
    "whitefield":        {"population_density": "medium",  "infra_score": 0.6},
    "electronic city":   {"population_density": "medium",  "infra_score": 0.65},
    "dharavi":           {"population_density": "high",   "infra_score": 0.25},
    "anand vihar":       {"population_density": "high",   "infra_score": 0.45},
}

DENSITY_SCORE = {"low": 0.2, "medium": 0.5, "high": 0.9}

DEFAULT_DEMOGRAPHIC_SCORE = 0.5  # neutral, for areas not in our dataset

# Rebalanced weights — must sum to 1.0
VOLUME_WEIGHT = 0.3
URGENCY_WEIGHT = 0.3
CATEGORY_WEIGHT_FACTOR = 0.2
DEMOGRAPHIC_WEIGHT = 0.2

VOLUME_CAP = 10


def get_demographic_score(location_text: str | None) -> float:
    """
    Look up population density + infra weakness for a free-text location.
    Matches by substring against our known-areas dataset (case-insensitive).
    Falls back to a neutral score if the area isn't in our dataset —
    this is a real limitation for a prototype: only seeded areas get
    a real demographic signal, everything else gets a neutral default.
    """
    if not location_text:
        return DEFAULT_DEMOGRAPHIC_SCORE

    lowered = location_text.lower()
    for area_name, data in AREA_DEMOGRAPHICS.items():
        if area_name in lowered:
            density_score = DENSITY_SCORE.get(data["population_density"], 0.5)
            infra_need_score = 1 - data["infra_score"]  # invert: weaker infra = higher need
            return round((density_score + infra_need_score) / 2, 2)

    return DEFAULT_DEMOGRAPHIC_SCORE


def compute_priority_score(
    request_count: int,
    max_urgency: str,
    top_category: str,
    location_text: str | None = None,
) -> float:
    """
    Combine volume, urgency, category, and demographic/infrastructure
    context into a single 0-100 priority score.
    """
    volume_score = min(request_count / VOLUME_CAP, 1.0)
    urgency_score = URGENCY_RANK.get(max_urgency, 0) / 2
    category_score = CATEGORY_WEIGHT.get(top_category, 0.2)
    demographic_score = get_demographic_score(location_text)

    raw_score = (
        volume_score * VOLUME_WEIGHT
        + urgency_score * URGENCY_WEIGHT
        + category_score * CATEGORY_WEIGHT_FACTOR
        + demographic_score * DEMOGRAPHIC_WEIGHT
    )
    return round(raw_score * 100, 1)


def detect_hotspots(requests: list) -> list[dict]:
    """
    Cluster geocoded citizen requests into hotspots using DBSCAN,
    then score each hotspot by priority — fusing report volume, urgency,
    issue category, and area-level demographic/infrastructure context.
    """
    geocoded = [r for r in requests if r.latitude is not None and r.longitude is not None]

    if len(geocoded) < MIN_REQUESTS_PER_HOTSPOT:
        return []

    coords = np.radians([[r.latitude, r.longitude] for r in geocoded])
    eps_radians = CLUSTER_RADIUS_KM / EARTH_RADIUS_KM

    db = DBSCAN(
        eps=eps_radians,
        min_samples=MIN_REQUESTS_PER_HOTSPOT,
        metric="haversine",
    ).fit(coords)

    labels = db.labels_

    hotspots = []
    for cluster_id in set(labels):
        if cluster_id == -1:
            continue

        members = [geocoded[i] for i in range(len(geocoded)) if labels[i] == cluster_id]

        avg_lat = sum(r.latitude for r in members) / len(members)
        avg_lon = sum(r.longitude for r in members) / len(members)

        categories = Counter(r.category for r in members if r.category)
        top_category = categories.most_common(1)[0][0] if categories else "general"

        max_urgency = max(
            (r.urgency for r in members if r.urgency),
            key=lambda u: URGENCY_RANK.get(u, 0),
            default="low",
        )

        # Use the most common location text among members to look up
        # demographic/infra context for this hotspot's area
        location_texts = Counter(r.location_text for r in members if r.location_text)
        representative_location = location_texts.most_common(1)[0][0] if location_texts else None

        priority_score = compute_priority_score(
            len(members), max_urgency, top_category, representative_location
        )

        hotspots.append({
            "center_latitude": avg_lat,
            "center_longitude": avg_lon,
            "request_count": len(members),
            "top_category": top_category,
            "max_urgency": max_urgency,
            "demographic_score": get_demographic_score(representative_location),
            "priority_score": priority_score,
            "request_ids": [r.id for r in members],
        })

    hotspots.sort(key=lambda h: h["priority_score"], reverse=True)
    return hotspots