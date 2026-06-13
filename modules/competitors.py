import re
from collections import Counter
from models import VisibilityResult

KNOWN_BRANDS = [
    "Seed", "Bioma", "Pendulum", "Begin Health", "BelliWelli",
    "Garden of Life", "Culturelle", "Align", "Florastor", "Renew Life",
    "Ritual", "MegaFood", "Thorne", "Pure Encapsulations", "Jarrow",
    "NOW Foods", "Solgar", "Natren", "VSL#3", "Visbiome",
    "Klaire Labs", "Seeking Health", "Life Extension", "Nature's Way",
    "Hyperbiotics", "Physician's Choice", "NewRhythm",
    "Bio-Kult", "Probiotic America", "Flora", "Ther-Biotic",
    "Custom Probiotics", "Dr. Formulated", "Lactobacillus",
]

STOP_WORDS = {
    "The", "This", "That", "These", "Those", "There", "Their", "When",
    "While", "With", "From", "Into", "Also", "Some", "Many", "More",
    "Most", "Here", "They", "Your", "You", "For", "And", "But", "Not",
    "All", "Any", "Both", "Each", "Few", "Such", "Than", "Too", "Very",
    "Just", "As", "At", "By", "In", "Is", "It", "Of", "On", "Or",
    "So", "Up", "Be", "Do", "Go", "If", "Me", "My", "No", "To", "We",
    "Its", "Are", "Has", "Had", "Can", "May", "Will", "Should", "Could",
    "Would", "Been", "Have", "Make", "Made", "Help", "Good", "Best",
    "High", "Low", "Well", "New", "Also", "Other", "Health", "Gut",
    "Probiotic", "Probiotics", "Supplement", "Supplements", "Product",
    "Products", "Brand", "Brands", "Overall", "Including", "Contains",
}


def aggregate_competitors(visibility: VisibilityResult, brand_name: str) -> dict[str, int]:
    # Drop failed API responses before processing
    clean_responses = [r for r in visibility.raw_responses if not r.startswith("FAILED:")]
    visibility = visibility.model_copy(update={"raw_responses": clean_responses})
    all_text = " ".join(visibility.raw_responses)
    counts = Counter()

    for brand in KNOWN_BRANDS:
        matches = re.findall(re.escape(brand), all_text, re.IGNORECASE)
        if matches:
            counts[brand] += len(matches)

    for word, count in Counter(
        re.findall(r'\b[A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{3,})?\b', all_text)
    ).items():
        if count >= 3 and word not in STOP_WORDS and word.lower() != brand_name.lower():
            if word not in counts:
                counts[word] = count

    result = {k: v for k, v in counts.items() if k.lower() != brand_name.lower()}
    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:15])
