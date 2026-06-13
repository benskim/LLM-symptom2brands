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
            if attempt < max_retries - 1:
                time.sleep(delays[attempt])
            else:
                return ""
    return ""


def analyze_evidence_gaps(
    brand_name: str,
    brand_website: str,
    visibility: VisibilityResult,
    citations: CitationResult,
    competitors: dict[str, int],
    grounding: GroundingResult,
) -> tuple[list[EvidenceGap], list[str]]:

    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.GenerationConfig(temperature=0),
    )

    prompt = f"""You are an AI visibility analyst. Analyze this data and identify evidence gaps.

BRAND: {brand_name}
WEBSITE: {brand_website}

VISIBILITY DATA:
- Visibility Score: {visibility.visibility_score}%
- Mentions: {visibility.mentions} out of {visibility.samples} AI responses

TOP COMPETITORS (brand: mention_count):
{json.dumps(dict(list(competitors.items())[:5]), indent=2)}

CITATION DATA:
- Brand domain citations: {citations.brand_domain_mentions}
- Total citations found: {citations.total_citation_mentions}
- Citation share: {citations.citation_share}%
- Top cited domains: {citations.top_domains[:5]}

GROUNDING:
- Static knowledge mentions: {grounding.static_mentions}
- Web-sourced mentions: {grounding.web_mentions}

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
