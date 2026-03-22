# agents/debate.py

def performance_agent(content):
    """
    Focus: Improve engagement, emotional appeal, CTA
    """

    improved_content = content

    # 1. Add emotional hook
    if not any(word in content.lower() for word in ["discover", "unlock", "introducing"]):
        improved_content = "Discover " + improved_content

    # 2. Add CTA if missing
    if not any(word in content.lower() for word in ["join", "start", "explore"]):
        improved_content += " Start your financial journey today!"

    # 3. Make it more conversational
    if "." in improved_content:
        improved_content = improved_content.replace(".", "!")

    # 4. Add urgency
    if "today" not in improved_content.lower():
        improved_content += " Don't miss out!"

    return {
        "agent": "performance",
        "feedback": "Enhanced emotional appeal, urgency, and CTA for higher engagement.",
        "suggested_content": improved_content,
        "score": 85
    }


def compliance_agent(content):
    """
    Focus: Ensure content is safe and compliant
    """

    risky_words = ["guaranteed", "100%", "risk-free", "instant profit"]
    flagged = []
    cleaned_content = content

    for word in risky_words:
        if word in content.lower():
            flagged.append(word)
            cleaned_content = cleaned_content.replace(word, "potential")

    return {
        "agent": "compliance",
        "feedback": f"Checked compliance. Flagged terms: {flagged}" if flagged else "Content is compliant.",
        "suggested_content": cleaned_content,
        "score": 90 if not flagged else 60
    }


def judge_agent(original_content, perf, comp):
    """
    Final decision maker: balances engagement vs compliance
    """

    if comp["score"] < 70:
        final = comp["suggested_content"]
        reason = "Compliance issues detected, prioritizing safe content."
    else:
        final = perf["suggested_content"]
        reason = "Content is compliant, optimized for engagement."

    return {
        "final_content": final,
        "reason": reason
    }