import httpx
import os
from app.config import GEMINI_API_KEY

class LLMClient:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment variables.")
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
            response = await client.post(
                f"{self.api_url}?key={GEMINI_API_KEY}",
                json=payload,
                headers=self.headers,
                timeout=60
            )
            response.raise_for_status()
            response_data = response.json()
            # Extracting the text from the nested structure
            llm_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
            # Remove markdown code fences if present
            if llm_text.startswith("```json") and llm_text.endswith("```"):
                llm_text = llm_text[7:-3].strip()
            return llm_text
