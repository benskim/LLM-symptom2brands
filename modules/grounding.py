import re
from models import VisibilityResult, GroundingResult

WEB_SIGNALS = [
    "according to", "source:", "cited from", "reference:", "published on",
    "study from", "research by", "as reported", "per ", "from the",
    "http", "www.", ".com", ".org", ".gov", ".edu",
    "article", "blog", "website", "page", "link",
]

STATIC_SIGNALS = [
    "generally", "typically", "in general", "most people", "many studies",
    "research suggests", "evidence indicates", "experts say",
    "it is known", "commonly", "often recommended",
    "clinical trials", "meta-analysis", "systematic review",
    "randomized controlled", "double-blind", "placebo",
]


def classify_grounding(visibility: VisibilityResult) -> GroundingResult:
    all_text = " ".join(visibility.raw_responses).lower()

    web_count = sum(all_text.count(signal.lower()) for signal in WEB_SIGNALS)
    static_count = sum(all_text.count(signal.lower()) for signal in STATIC_SIGNALS)

    return GroundingResult(
        static_mentions=static_count,
        web_mentions=web_count,
    )
