import re
from collections import Counter
from urllib.parse import urlparse
from models import VisibilityResult, CitationResult

AUTHORITY_DOMAINS = [
    "healthline.com", "webmd.com", "medicalnewstoday.com", "nih.gov",
    "ncbi.nlm.nih.gov", "mayoclinic.org", "health.harvard.edu",
    "nccih.nih.gov", "examine.com", "pubmed.ncbi.nlm.nih.gov",
    "reddit.com", "amazon.com", "consumerlab.com", "labdoor.com",
    "verywellhealth.com", "everydayhealth.com", "mindbodygreen.com",
    "draxe.com", "wellnessmama.com", "healthgrades.com",
]

URL_PATTERN = re.compile(
    r'https?://(?:www\.)?([a-zA-Z0-9\-]+\.[a-zA-Z]{2,})(?:/[^\s\)\"\']*)?'
)

DOMAIN_PATTERN = re.compile(
    r'\b(?:www\.)?([a-zA-Z0-9\-]+\.(?:com|org|gov|edu|net|io))\b',
    re.IGNORECASE
)


def extract_citations(visibility: VisibilityResult, brand_website: str) -> CitationResult:
    all_text = " ".join(visibility.raw_responses)
    domain_counts = Counter()

    url_matches = URL_PATTERN.findall(all_text)
    for domain in url_matches:
        domain_counts[domain.lower()] += 1

    domain_matches = DOMAIN_PATTERN.findall(all_text)
    for domain in domain_matches:
        domain_counts[domain.lower()] += 1

    for domain in AUTHORITY_DOMAINS:
        if domain in all_text.lower() and domain not in domain_counts:
            domain_counts[domain] = all_text.lower().count(domain)

    brand_domain = ""
    if brand_website:
        try:
            parsed = urlparse(brand_website if brand_website.startswith("http") else f"https://{brand_website}")
            brand_domain = parsed.netloc.replace("www.", "").lower()
        except Exception:
            pass

    total_mentions = sum(domain_counts.values())
    brand_mentions = domain_counts.get(brand_domain, 0) if brand_domain else 0

    citation_share = round((brand_mentions / total_mentions) * 100, 1) if total_mentions > 0 else 0.0

    top_domains = [d for d, _ in domain_counts.most_common(10)]

    return CitationResult(
        top_domains=top_domains,
        domain_counts=dict(domain_counts.most_common(10)),
        citation_share=citation_share,
        brand_domain_mentions=brand_mentions,
        total_citation_mentions=total_mentions,
    )
