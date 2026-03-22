import json

from sympy import content
from memory.vector_store import check_brand_similarity

def risk_confidence_score(content):
    
    score = {
        "brand_alignment": 0,
        "compliance_risk": 0,
        "engagement_score": 0
    }

    # Load rules
    with open("data/compliance_rules.json") as f:
        rules = json.load(f)

    # Compliance Risk
    for phrase in rules["banned_phrases"]:
        if phrase in content:
            score["compliance_risk"] += 50

    if score["compliance_risk"] == 0:
        score["compliance_risk"] = 10  # low base risk

    # Brand Alignment (simple keyword logic)
    similarity = check_brand_similarity(content)
    score["brand_alignment"] = int(similarity * 100)

    # Engagement Score (based on tone)
    # Engagement Score (smarter logic)
    engagement = 50

    if "!" in content:
        engagement += 15

    if any(word in content.lower() for word in ["discover", "unlock", "introducing"]):
        engagement += 15

    if any(word in content.lower() for word in ["join", "start", "explore"]):
        engagement += 10

    if len(content.split()) > 12:
        engagement += 10

    score["engagement_score"] = min(engagement, 100)

    return score