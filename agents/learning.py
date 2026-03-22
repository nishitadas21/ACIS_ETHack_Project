# agents/learning.py

import json
from memory.vector_store import get_most_similar

def load_feedback():
    try:
        with open("memory/feedback.json", "r") as f:
            return json.load(f)
    except:
        return []

def learning_agent(current_prompt):

    feedback_data = load_feedback()

    if not feedback_data:
        return {
            "insight": "No past data available",
            "suggestion": ""
        }

    past_contents = [item["content"] for item in feedback_data]

    similar = get_most_similar(current_prompt, past_contents)

    score = {}

    for item in feedback_data:
        if item["content"] == similar:
            score = item["scores"]
            break

    insight = "Previous similar content had: "

    if score:
        insight += f"Brand {score.get('brand',0)}%, Engagement {score.get('engagement',0)}%"
    else:
        insight += "No score data."

    suggestion = ""

    if score.get("engagement", 0) < 70:
        suggestion += "Make content more engaging with CTA. "

    if score.get("brand", 0) < 70:
        suggestion += "Align more with professional tone."

    return {
        "insight": insight,
        "suggestion": suggestion
    }