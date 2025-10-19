import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

try:
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content("test")
    print("✅ gemini-2.5-flash WORKS!")
    print(response.text)
except Exception as e:
    print(f"❌ gemini-2.5-flash FAILED: {e}")
    print("\n🔄 Trying gemini-1.5-flash instead...")
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content("test")
    print("✅ gemini-1.5-flash WORKS!")
