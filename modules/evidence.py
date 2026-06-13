import time
import json
import os
import google.generativeai as genai
from models import (
    VisibilityResult, CitationResult, GroundingResult, EvidenceGap
)


def _call_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    delays = [1, 2, 4]
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
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

    api_key = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config=genai.GenerationConfig(temperature=0),
    )

    top_competitors = list(competitors.items())[:5]
    top_domains = citations.top_domains[:5]

    prompt = f"""You are an AI visibility analyst. Analyze this data and identify evidence gaps.

BRAND: {brand_name}
WEBSITE: {brand_website}

VISIBILITY DATA:
- Visibility Score: {visibility.visibility_score}%
- Mentions: {visibility.mentions} out of {visibility.samples} AI responses

TOP COMPETITORS (brand: mention_count):
{json.dumps(dict(top_competitors), indent=2)}

CITATION DATA:
- Brand domain citations: {citations.brand_domain_mentions}
- Total citations found: {citations.total_citation_mentions}
- Citation share: {citations.citation_share}%
- Top cited domains: {top_domains}

GROUNDING:
- Static knowledge mentions: {grounding.static_mentions}
- Web-sourced mentions: {grounding.web_mentions}

RULES:
- Never invent facts not supported by the data above.
- Use language like "Possible gap", "Likely gap", "Observed difference".
- NEVER say "Root cause", "Guaranteed explanation", "Definitive reason".
- Be specific and evidence-backed.

Return a JSON object with this exact structure:
{{
  "evidence_gaps": [
    {{
      "gap_type": "string (e.g. authority_signals, brand_mentions, citation_presence, content_coverage)",
      "confidence": "string (low|medium|high)",
      "evidence": ["list", "of", "specific", "evidence", "strings"]
    }}
  ],
  "quick_wins": [
    "actionable recommendation string 1",
    "actionable recommendation string 2"
  ]
}}

Generate 3-5 evidence gaps and exactly 10 quick wins prioritized by impact.
Quick wins should be specific, actionable steps for a Shopify gut health brand.
"""

    raw = _call_with_retry(model, prompt)

    try:
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1])
        data = json.loads(clean)
    except Exception:
        import re
        json_match = re.search(r'\{[\s\S]+\}', raw)
        if json_match:
            try:
                data = json.loads(json_match.group())
            except Exception:
                data = {"evidence_gaps": [], "quick_wins": []}
        else:
            data = {"evidence_gaps": [], "quick_wins": []}

    gaps = []
    for g in data.get("evidence_gaps", []):
        try:
            gaps.append(EvidenceGap(**g))
        except Exception:
            pass

    quick_wins = data.get("quick_wins", [])[:10]

    return gaps, quick_wins
