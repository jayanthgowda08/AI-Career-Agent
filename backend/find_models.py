"""
Run this script to find which Gemini models actually work with your API key.
Usage: .\venv\Scripts\python.exe find_models.py
"""
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("GEMINI_API_KEY")

# Models the API error messages recommend
CANDIDATES = [
    "gemini-3.8-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

API_VERSIONS = ["v1beta", "v1"]

print(f"Testing API key: {key[:12]}...\n")
print(f"{'Model':<30} {'API v1beta':<20} {'API v1':<20}")
print("-" * 70)

for model in CANDIDATES:
    results = []
    for api_ver in API_VERSIONS:
        try:
            client = genai.Client(api_key=key, http_options={"api_version": api_ver})
            resp = client.models.generate_content(
                model=model,
                contents="Reply with the word OK only.",
                config=types.GenerateContentConfig(temperature=0),
            )
            text = (resp.text or "").strip()[:20]
            results.append(f"✅ {text}")
        except Exception as e:
            err = str(e)
            if "404" in err:
                results.append("❌ 404 not found")
            elif "429" in err:
                results.append("⚠️ 429 quota")
            elif "503" in err:
                results.append("⚠️ 503 overload")
            else:
                results.append(f"❌ {err[:25]}")

    print(f"{model:<30} {results[0]:<30} {results[1]:<30}")

print("\nDone. Use a ✅ model in your .env as GEMINI_MODEL=...")
