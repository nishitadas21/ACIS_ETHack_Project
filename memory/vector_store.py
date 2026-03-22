from sentence_transformers import SentenceTransformer
import numpy as np
import json

model = SentenceTransformer('all-MiniLM-L6-v2')


def get_similarity(text1, text2):
    emb1 = model.encode(text1)
    emb2 = model.encode(text2)
    
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    return similarity


def load_past_content():
    try:
        with open("memory/feedback.json", "r") as f:
            data = json.load(f)
            return [item["content"] for item in data]
    except:
        return []


def check_brand_similarity(content):
    past_contents = load_past_content()
    
    if not past_contents:
        return 0.5  # neutral if no history
    
    similarities = []
    
    for past in past_contents:
        sim = get_similarity(content, past)
        similarities.append(sim)
    
    return max(similarities)

def get_most_similar(query_text, past_contents):
    if not past_contents:
        return None
    
    # Encode the current query
    query_emb = model.encode(query_text)
    
    best_match = None
    highest_sim = -1
    
    for content in past_contents:
        content_emb = model.encode(content)
        # Calculate Cosine Similarity
        sim = np.dot(query_emb, content_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(content_emb))
        
        if sim > highest_sim:
            highest_sim = sim
            best_match = content
            
    return best_match