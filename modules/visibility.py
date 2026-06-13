import time
import os
import google.generativeai as genai
from models import VisibilityResult

SAMPLES_PER_PROMPT = 5
CALL_DELAY = 2.5   # 24 RPM — safely under the 30 RPM free-tier limit


def _call_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "ResourceExhausted" in type(e).__name__:
                wait = 60
                print(f"    ⏳ Rate limit hit — waiting {wait}s before retry {attempt+1}/{max_retries}…")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                time.sleep(delays[attempt])
            else:
                return f"FAILED: {msg}"
    return "FAILED"


def run_visibility_sampling(brand_name: str, prompts: list[str]) -> VisibilityResult:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    # Use flash-lite for bulk sampling: 30 RPM / 1500 RPD free tier
    model = genai.GenerativeModel("gemini-2.0-flash-lite")

    raw_responses = []
    mentions = 0
    total_samples = 0

    for i, prompt in enumerate(prompts, 1):
        print(f"  Prompt {i}/{len(prompts)}: \"{prompt}\"")
        for s in range(SAMPLES_PER_PROMPT):
            text = _call_with_retry(model, prompt)
            raw_responses.append(text)
            total_samples += 1
            if brand_name.lower() in text.lower():
                mentions += 1
            time.sleep(CALL_DELAY)

    score = round((mentions / total_samples) * 100, 1) if total_samples > 0 else 0.0

    return VisibilityResult(
        brand_name=brand_name,
        visibility_score=score,
        mentions=mentions,
        samples=total_samples,
        raw_responses=raw_responses,
    )
