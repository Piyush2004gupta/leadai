import requests
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "https://2f16-27-123-248-66.ngrok-free.app")  # ngrok URL default fallback

def generate_text(prompt, model="tinyllama"):
    """
    Common helper for Ollama generation.
    """
    try:
        res = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False   # 🔥 IMPORTANT
            },
            timeout=30
        )
        res.raise_for_status()
        return res.json().get("response", "")
    except Exception as e:
        print(f"Ollama Error: {e}")
        return ""
