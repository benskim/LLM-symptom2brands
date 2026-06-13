import time
import os
import google.generativeai as genai
from models import VisibilityResult

PROMPTS = [
    "What are the best probiotics for bloating?",
    "What supplements help with constipation?",
    "Best digestive support products for kids",
    "Top gut health products for families",
    "Best probiotics for IBS symptoms",
]

SAMPLES_PER_PROMPT = 5


def _call_gemini_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delays[attempt])
            else:
                return f"FAILED: {str(e)}"
    return "FAILED"


def run_visibility_sampling(brand_name: str) -> VisibilityResult:
    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    raw_responses = []
    mentions = 0
    total_samples = 0

    for prompt in PROMPTS:
        for _ in range(SAMPLES_PER_PROMPT):
            response_text = _call_gemini_with_retry(model, prompt)
            raw_responses.append(response_text)
            total_samples += 1
            if brand_name.lower() in response_text.lower():
                mentions += 1

    visibility_score = round((mentions / total_samples) * 100, 1) if total_samples > 0 else 0.0

    return VisibilityResult(
        brand_name=brand_name,
        visibility_score=visibility_score,
        mentions=mentions,
        samples=total_samples,
        raw_responses=raw_responses,
    )
