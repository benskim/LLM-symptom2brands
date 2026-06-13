import re
from collections import Counter
from models import VisibilityResult

KNOWN_BRANDS = [
    "Seed", "Bioma", "Pendulum", "Begin Health", "BelliWelli",
    "Garden of Life", "Culturelle", "Align", "Florastor", "Renew Life",
    "Ritual", "MegaFood", "Thorne", "Pure Encapsulations", "Jarrow",
    "NOW Foods", "Solgar", "Natren", "VSL#3", "Visbiome",
    "Klaire Labs", "Seeking Health", "Life Extension", "Nature's Way",
    "Hyperbiotics", "Physician's Choice", "NewRhythm", "Lactobacillus",
    "Bio-Kult", "Probiotic America", "Flora", "Ther-Biotic",
    "Custom Probiotics", "Naturo Sciences", "Dr. Formulated",
]


def aggregate_competitors(visibility: VisibilityResult, brand_name: str) -> dict[str, int]:
    all_text = " ".join(visibility.raw_responses)
    counts = Counter()

    for brand in KNOWN_BRANDS:
        pattern = re.compile(re.escape(brand), re.IGNORECASE)
        found = pattern.findall(all_text)
        if found:
            counts[brand] += len(found)

    words = re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\b', all_text)
    word_counts = Counter(words)

    stop_words = {
        "The", "This", "That", "These", "Those", "There", "Their",
        "When", "While", "With", "From", "Into", "Also", "Some",
        "Many", "More", "Most", "Here", "They", "Your", "You",
        "For", "And", "But", "Not", "All", "Any", "Both",
        "Each", "Few", "More", "Such", "Than", "Too", "Very",
        "Just", "As", "At", "By", "In", "Is", "It", "Its",
        "Of", "On", "Or", "So", "Up", "Be", "Do", "Go",
        "If", "Me", "My", "No", "To", "We",
    }

    for word, count in word_counts.items():
        if (
            count >= 3
            and word not in stop_words
            and word.lower() != brand_name.lower()
            and len(word) > 3
        ):
            if word not in counts:
                counts[word] = count

    brand_lower = brand_name.lower()
    result = {k: v for k, v in counts.items() if k.lower() != brand_lower}
    return dict(sorted(result.items(), key=lambda x: x[1], reverse=True)[:15])
