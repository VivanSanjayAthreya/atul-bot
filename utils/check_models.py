import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Asking Google what this API Key can do...")
try:
    for m in genai.list_models():
        if 'embedContent' in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"❌ API Key Error: {e}")