import os
import json
import faiss
import numpy as np
import gradio as gr
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from google import generativeai as genai

# --- Load environment variables ---
load_dotenv()

# --- Google Gemini Setup ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set in environment variables (.env file).")

genai.configure(api_key=GEMINI_API_KEY)
gemini_model_name = "gemini-2.0-flash"

# --- Gemini Helper Functions ---
def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel(gemini_model_name)
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error in Gemini API call: {e}")
        return "Sorry, I couldn't process your request right now."

def expand_query_with_gemini(user_query):
    prompt = f"""Expand the following search query and suggest related topics if possible:

Query: "{user_query}"

Return expanded query and some related topics (comma separated).
"""
    return ask_gemini(prompt)

def generate_final_report(context, query):
    prompt = f"""You are a helpful assistant reading a PDF. Given the following extracted content, answer the user's query specifically based on the provided information.

Context:
{context}

Query:
{query}

Answer:"""
    return ask_gemini(prompt)

# --- Load Pre-Saved FAISS Index and Chunks ---
def load_faiss_index(index_path):
    index = faiss.read_index(index_path)
    return index

def load_chunks(json_path):
    with open(json_path, 'r') as f:
        chunks = json.load(f)
    return chunks

# --- FAISS Search ---
def search_faiss(expanded_query, index, chunks, embedder, top_k=5):
    query_embedding = embedder.encode([expanded_query])
    D, I = index.search(np.array(query_embedding).astype(np.float32), top_k)
    results = [chunks[i] for i in I[0]]
    return results

# --- Full Pipeline ---
def full_pipeline(user_query, index, chunks, embedder):
    expanded_info = expand_query_with_gemini(user_query)
    print(f"🔍 Expanded Query and Topics: {expanded_info}")

    retrieved_chunks = search_faiss(expanded_info, index, chunks, embedder)
    context = "\n\n".join(retrieved_chunks)

    final_answer = generate_final_report(context, user_query)
    return final_answer

# --- Gradio Interface ---
def create_interface(index, chunks, embedder):
    def chatbot(user_query):
        return full_pipeline(user_query, index, chunks, embedder)

    iface = gr.Interface(
        fn=chatbot,
        inputs="text",
        outputs="text",
        title="📚 Smart PDF Chatbot (Prebuilt)",
        description="Ask anything about your PDFs. Powered by Gemini + FAISS semantic search."
    )
    return iface

# --- Main Run ---
def main():
    # Paths to your precomputed files
    index_path = "faiss_index.faiss"
    chunks_path = "chunks.json"

    # --- Load Everything ---
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index file not found at: {index_path}")

    if not os.path.exists(chunks_path):
        raise FileNotFoundError(f"Chunks JSON file not found at: {chunks_path}")

    index = load_faiss_index(index_path)
    smart_chunks = load_chunks(chunks_path)

    # --- Load SentenceTransformer model ---
    embedder_model = SentenceTransformer('all-MiniLM-L6-v2')

    print("✅ FAISS and Chunks loaded. Ready to Chat!")

    # --- Launch Gradio App ---
    gradio_app = create_interface(index, smart_chunks, embedder_model)
    gradio_app.launch(server_name="0.0.0.0", server_port=7860)

if __name__ == "__main__":
    main()