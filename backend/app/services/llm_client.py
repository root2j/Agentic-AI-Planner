import httpx
import os
import asyncio # Import asyncio
from app.config import GEMINI_API_KEY

class LLMClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. LLM calls will likely fail or be very fast.")
            # For testing, we might want to raise an error, but for now, let's just warn.
            # raise ValueError("GEMINI_API_KEY not set in environment variables.")
        else:
            print(f"GEMINI_API_KEY is set (first 5 chars): {GEMINI_API_KEY[:5]}*****")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.headers = {
            "Content-Type": "application/json"
        }

    async def send_prompt(self, prompt: str) -> str:
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }
        async with httpx.AsyncClient() as client:
            retries = 3
            for i in range(retries):
                try:
                    response = await client.post(
                        f"{self.api_url}?key={GEMINI_API_KEY}",
                        json=payload,
                        headers=self.headers,
                        timeout=60
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    break # If successful, break the loop
                except httpx.HTTPStatusError as e:
                    if i < retries - 1 and e.response.status_code in [500, 502, 503, 504]:
                        print(f"LLM API call failed with {e.response.status_code}. Retrying in {2**(i+1)} seconds...")
                        await asyncio.sleep(2**(i+1)) # Exponential backoff
                    else:
                        raise # Re-raise the last exception if all retries fail or it's not a retryable error
            
            # Add a small delay to avoid rate limiting after a successful call
            await asyncio.sleep(1)
            # Extracting the text from the nested structure
            llm_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            # Remove markdown code fences if present
            if llm_text.startswith("```json") and llm_text.endswith("```"):
                llm_text = llm_text[7:-3].strip()
            return llm_text
