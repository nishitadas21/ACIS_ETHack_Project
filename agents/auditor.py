import json

def check_compliance(content):
    with open("data/compliance_rules.json") as f:
        rules = json.load(f)
    
    issues = []
    for phrase in rules["banned_phrases"]:
        if phrase in content:
            issues.append(phrase)
    
    return issues