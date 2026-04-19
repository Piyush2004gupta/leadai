import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "tinyllama"

def generate_text(prompt, model_name=MODEL_NAME):
    """
    Helper to generate text using local Ollama instance.
    """
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        print(f"Ollama Error: {e}")
        return ""
