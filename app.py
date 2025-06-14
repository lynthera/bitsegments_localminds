from flask import Flask, request, jsonify, render_template
from llama_cpp import Llama
import uuid
from flask_cors import CORS
from memory import load_memory, save_memory, get_relevant_context
import glob
import os

app = Flask(__name__, template_folder="templates")
CORS(app)

def find_gguf_model(model_dir):
    gguf_files = glob.glob(os.path.join(model_dir, "*.gguf"))
    if not gguf_files:
        raise FileNotFoundError(f"No .gguf model found in {model_dir}")
    return gguf_files[0]

model_path = find_gguf_model("models")

llm = Llama(
    model_path=model_path,
    n_ctx=2048,
    n_threads=4,
    n_gpu_layers=0
)

SYSTEM_PROMPT = "You are a concise assistant. Always answer clearly and directly."

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "").strip()
    session_id = data.get("session_id", str(uuid.uuid4()))
    chat_id = str(data.get("chat_id", "default"))

    if not user_input:
        return jsonify({"response": "⚠️ Empty message.", "session_id": session_id, "chat_id": chat_id})

    memory_context = get_relevant_context(session_id, chat_id, user_input)
    history = [f"User: {m['user']}\nAssistant: {m['assistant']}" for m in memory_context]
    memory_prompt = "\n".join(history)

    if not memory_context:
        full_prompt = f"System: {SYSTEM_PROMPT}\nUser: {user_input}\nAssistant:"
    else:
        full_prompt = f"{memory_prompt}\nUser: {user_input}\nAssistant:"

    try:
        output = llm(full_prompt, max_tokens=1564, stop=["User:", "Assistant:"])
        text = output["choices"][0]["text"].strip()
    except Exception as e:
        return jsonify({"response": f"❌ Model error: {str(e)}", "session_id": session_id, "chat_id": chat_id})

    memory = load_memory(session_id, chat_id)
    memory.append({"user": user_input, "assistant": text})
    save_memory(session_id, chat_id, memory)

    return jsonify({"response": text, "session_id": session_id, "chat_id": chat_id})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
