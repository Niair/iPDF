import os
from dotenv import load_dotenv

load_dotenv()

print("🧪 Testing Models...\n")

# Test Groq
print("1️⃣ Testing Groq API...")
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    models_to_test = [
        "openai/gpt-oss-20b",  # From your screenshot
        "llama-3.1-70b-versatile",  # Recommended
        "llama-3.1-8b-instant"  # Fastest
    ]
    
    for model in models_to_test:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=10
            )
            print(f"   ✅ {model} - WORKS!")
        except Exception as e:
            print(f"   ❌ {model} - FAILED: {str(e)[:50]}")
except Exception as e:
    print(f"   ❌ Groq setup failed: {e}")

print("\n2️⃣ Testing Google Gemini...")
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    
    models_to_test = [
        "gemini-2.5-flash",  # From your screenshot
        "gemini-2.0-flash-exp",  # Experimental
        "gemini-1.5-flash",  # Recommended
        "gemini-1.5-pro"  # High quality
    ]
    
    for model_name in models_to_test:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("hi")
            print(f"   ✅ {model_name} - WORKS!")
        except Exception as e:
            print(f"   ❌ {model_name} - FAILED: {str(e)[:50]}")
except Exception as e:
    print(f"   ❌ Gemini setup failed: {e}")

print("\n✅ Test complete!")
