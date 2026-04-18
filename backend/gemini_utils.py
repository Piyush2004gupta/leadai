import google.generativeai as genai
import os

GEMINI_API_KEY = "AIzaSyD8xyn5RPPRWa38FNZ6INX2xnShw-1uWIA"

genai.configure(api_key=GEMINI_API_KEY)

def generate_text(prompt, model_name="gemini-1.5-flash"):
    """
    Common helper for Gemini generation.
    """
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return ""
