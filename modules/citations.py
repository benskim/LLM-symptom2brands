import re
from collections import Counter
from urllib.parse import urlparse
from models import VisibilityResult, CitationResult

URL_RE = re.compile(r'https?://(?:www\.)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})(?:/[^\s\)\"\']*)?' )
DOMAIN_RE = re.compile(r'\b(?:www\.)?([a-zA-Z0-9\-]+\.(?:com|org|gov|edu|net|io))\b', re.IGNORECASE)

AUTHORITY_DOMAINS = [
    "healthline.com", "webmd.com", "medicalnewstoday.com", "nih.gov",
    "ncbi.nlm.nih.gov", "mayoclinic.org", "health.harvard.edu",
    "examine.com", "pubmed.ncbi.nlm.nih.gov", "reddit.com",
    "consumerlab.com", "labdoor.com", "verywellhealth.com",
    "everydayhealth.com", "mindbodygreen.com",
]


def extract_citations(visibility: VisibilityResult, brand_website: str) -> CitationResult:
    all_text = " ".join(visibility.raw_responses)
    counts = Counter()

    for domain in URL_RE.findall(all_text):
        counts[domain.lower()] += 1
    for domain in DOMAIN_RE.findall(all_text):
        counts[domain.lower()] += 1
    for d in AUTHORITY_DOMAINS:
        n = all_text.lower().count(d)
        if n and d not in counts:
            counts[d] = n

    brand_domain = ""
    if brand_website:
        raw = brand_website if "://" in brand_website else f"https://{brand_website}"
        try:
            brand_domain = urlparse(raw).netloc.replace("www.", "").lower()
        except Exception:
            pass

    total = sum(counts.values())
    brand_hits = counts.get(brand_domain, 0) if brand_domain else 0
    share = round((brand_hits / total) * 100, 1) if total > 0 else 0.0

    top = dict(counts.most_common(10))
    return CitationResult(
        top_domains=list(top.keys()),
        domain_counts=top,
        citation_share=share,
        brand_domain_mentions=brand_hits,
        total_citation_mentions=total,
    )
