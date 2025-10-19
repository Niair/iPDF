from groq import Groq
import os
from dotenv import load_dotenv  # <-- import this to load the .env file

# Load environment variables from .env
load_dotenv()

# Now fetch the API key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

try:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("✅ openai/gpt-oss-20b WORKS!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"❌ openai/gpt-oss-20b FAILED: {e}")
    print("\n🔄 Trying llama-3.1-70b-versatile instead...")

    response = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=10
    )
    print("✅ llama-3.1-70b-versatile WORKS!")
    print(response.choices[0].message.content)
