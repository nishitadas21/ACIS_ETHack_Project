import json

def fix_content(content, issues):
    with open("data/compliance_rules.json") as f:
        rules = json.load(f)
    
    for issue in issues:
        if issue in rules["suggestions"]:
            content = content.replace(issue, rules["suggestions"][issue])
    
    return content