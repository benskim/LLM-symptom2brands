from models import VisibilityResult, GroundingResult

WEB_SIGNALS = [
    "according to", "source:", "cited from", "as reported", "per ",
    "http", "www.", ".com", ".org", ".gov", ".edu",
    "article", "blog", "website",
]

STATIC_SIGNALS = [
    "generally", "typically", "in general", "most people", "many studies",
    "research suggests", "evidence indicates", "experts say",
    "commonly", "often recommended", "clinical trials",
    "meta-analysis", "systematic review", "randomized controlled",
    "double-blind", "placebo",
]


def classify_grounding(visibility: VisibilityResult) -> GroundingResult:
    all_text = " ".join(visibility.raw_responses).lower()
    web = sum(all_text.count(s.lower()) for s in WEB_SIGNALS)
    static = sum(all_text.count(s.lower()) for s in STATIC_SIGNALS)
    return GroundingResult(static_mentions=static, web_mentions=web)
