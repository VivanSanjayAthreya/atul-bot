import google.generativeai as genai
import os
from dotenv import load_dotenv

# 1. Load your key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")
    exit()

# 2. Configure Google
genai.configure(api_key=api_key)

print(f"🔍 Checking available models for your API Key...")

try:
    found_any = False
    for m in genai.list_models():
        # We only care about models that can do "Embeddings"
        if 'embedContent' in m.supported_generation_methods:
            print(f"   ✅ AVAILABLE: {m.name}")
            found_any = True
            
    if not found_any:
        print("   ❌ No embedding models found. Check if 'Generative Language API' is enabled in Google Console.")

except Exception as e:
    print(f"   ❌ Connection Error: {e}")