import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ GEMINI_API_KEY not found in .env")
    exit(1)

try:
    client = genai.Client(api_key=api_key)
    print(f"✅ Client initialized. Listing models...")
    
    # List models (the exact method might depend on SDK version, assuming standard v1beta or similar)
    # in google-genai SDK (v1.x), it is usually client.models.list()
    
    for model in client.models.list():
        print(f"- {model.name}")
        
except Exception as e:
    print(f"❌ Error: {e}")
