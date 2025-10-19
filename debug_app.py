import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("🔍 DEBUGGING iPDF CONFIGURATION")
print("=" * 60)

# Check .env loading
print("\n1️⃣ Environment Variables:")
print(f"   GROQ_API_KEY: {'✅ Set' if os.getenv('GROQ_API_KEY') else '❌ Not Set'}")
print(f"   GROQ_MODEL: {os.getenv('GROQ_MODEL', 'Not Set')}")
print(f"   GOOGLE_API_KEY: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Not Set'}")
print(f"   GEMINI_MODEL: {os.getenv('GEMINI_MODEL', 'Not Set')}")

# Test Groq
print("\n2️⃣ Testing Groq Connection:")
try:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print(f"   ✅ Groq ({model}) working!")
except Exception as e:
    print(f"   ❌ Groq failed: {e}")

# Test Gemini
print("\n3️⃣ Testing Gemini Connection:")
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    model = genai.GenerativeModel(model_name)
    
    response = model.generate_content("test")
    print(f"   ✅ Gemini ({model_name}) working!")
except Exception as e:
    print(f"   ❌ Gemini failed: {e}")

# Test LLMHandler
print("\n4️⃣ Testing LLMHandler:")
try:
    import sys
    sys.path.insert(0, 'src')
    from core.llm_handler import LLMHandler
    
    llm = LLMHandler(provider="groq")
    result = llm.test_connection()
    print(f"   ✅ LLMHandler working! Provider: {llm.get_provider()}")
except Exception as e:
    print(f"   ❌ LLMHandler failed: {e}")

print("\n" + "=" * 60)
print("✅ Debug complete!")
print("=" * 60)
