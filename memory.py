import os
import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MEMORY_DIR = "./memory"
os.makedirs(MEMORY_DIR, exist_ok=True)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def _memory_path(session_id, chat_id):
    return os.path.join(MEMORY_DIR, f"{session_id}_{chat_id}.json")

def load_memory(session_id, chat_id):
    path = _memory_path(session_id, chat_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_memory(session_id, chat_id, memory):
    path = _memory_path(session_id, chat_id)
    with open(path, "w") as f:
        json.dump(memory[-20:], f)

def get_relevant_context(session_id, chat_id, current_input, top_k=3):
    memory = load_memory(session_id, chat_id)
    if not memory:
        return []

    corpus = [f"User: {item['user']}\nAssistant: {item['assistant']}" for item in memory]

    corpus_embeddings = embedder.encode(corpus, convert_to_tensor=True).cpu()
    query_embedding = embedder.encode([current_input], convert_to_tensor=True).cpu()

    similarities = cosine_similarity(query_embedding, corpus_embeddings)[0]
    top_indices = similarities.argsort()[-top_k:][::-1]

    return [memory[i] for i in top_indices]
