import openai
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("⚠️ WARNING: OPENAI_API_KEY is not set in environment!")

client = openai.OpenAI(api_key=OPENAI_API_KEY or "missing")

def generate_text(prompt, model_name="gpt-4o-mini"):
    """
    Common helper for OpenAI generation using gpt-4o-mini.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"OpenAI Error: {e}")
        return ""
