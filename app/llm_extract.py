# filepath: backend/app/llm_extract.py
# Use google-generativeai for Gemini LLM integration
import google.generativeai as genai
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

FNOL_PROMPT = """
Extract the following FNOL claim fields from the email:
- Claim Number
- Policy Holder
- Incident Date
- Loss Description

Email Body:
{body}
"""

def extract_fnol_fields_with_gemini(email_body: str) -> dict:
    print("GEMINI_API_KEY:", GEMINI_API_KEY)
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")
    prompt = FNOL_PROMPT.format(body=email_body)
    response = model.generate_content(prompt)
    # Stub: Parse response to dict (replace with actual parsing logic)
    import json
    try:
        fields = json.loads(response.text)
    except Exception:
        fields = {"raw_response": response.text}
    return fields
