import time
import json
import re
import os
import google.generativeai as genai
from models import VisibilityResult, CitationResult, GroundingResult, EvidenceGap


def _call_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            msg = str(e)
            if "429" in msg or "ResourceExhausted" in type(e).__name__:
                wait = 60
                print(f"    ⏳ Rate limit — waiting {wait}s before retry {attempt+1}/{max_retries}…")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                time.sleep(delays[attempt])
            else:
                return ""
    return ""


def analyze_evidence_gaps(
    brand_name: str,
    brand_website: str,
    visibility: VisibilityResult,
    citations: "CitationResult | None",
    competitors: dict[str, int],
    grounding: "GroundingResult | None",
) -> tuple[list[EvidenceGap], list[str]]:

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        generation_config=genai.GenerationConfig(temperature=0),
    )

    c_brand   = citations.brand_domain_mentions if citations else 0
    c_total   = citations.total_citation_mentions if citations else 0
    c_share   = citations.citation_share if citations else 0.0
    c_domains = citations.top_domains[:5] if citations else []
    g_static  = grounding.static_mentions if grounding else 0
    g_web     = grounding.web_mentions if grounding else 0

    prompt = f"""You are an AI visibility analyst. Analyze this data and identify evidence gaps.

BRAND: {brand_name}
WEBSITE: {brand_website}

VISIBILITY DATA:
- Visibility Score: {visibility.visibility_score}%
- Mentions: {visibility.mentions} out of {visibility.samples} AI responses

TOP COMPETITORS (brand: mention_count):
{json.dumps(dict(list(competitors.items())[:5]), indent=2)}

CITATION DATA:
- Brand domain citations: {c_brand}
- Total citations found: {c_total}
- Citation share: {c_share}%
- Top cited domains: {c_domains}

GROUNDING:
- Static knowledge mentions: {g_static}
- Web-sourced mentions: {g_web}

RULES:
- Never invent facts not in the data above.
- Use only: "Possible gap", "Likely gap", "Observed difference".
- NEVER say: "Root cause", "Guaranteed explanation", "Definitive reason".

Return ONLY valid JSON in this exact structure:
{{
  "evidence_gaps": [
    {{
      "gap_type": "authority_signals",
      "confidence": "medium",
      "evidence": ["specific evidence string 1", "specific evidence string 2"]
    }}
  ],
  "quick_wins": [
    "Specific actionable recommendation 1",
    "Specific actionable recommendation 2"
  ]
}}

Generate 3–5 evidence gaps. Generate exactly 10 quick wins prioritized by impact for a Shopify gut health brand."""

    raw = _call_with_retry(model, prompt)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = "\n".join(clean.split("\n")[1:-1])
        data = json.loads(clean)
    except Exception:
        m = re.search(r'\{[\s\S]+\}', raw)
        try:
            data = json.loads(m.group()) if m else {}
        except Exception:
            data = {}

    gaps = []
    for g in data.get("evidence_gaps", []):
        try:
            gaps.append(EvidenceGap(**g))
        except Exception:
            pass

    wins = data.get("quick_wins", [])[:10]
    return gaps, wins
