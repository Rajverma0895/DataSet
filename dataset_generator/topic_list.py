import json
from pathlib import Path
from typing import Dict, Iterable, List


topics: List[str] = [
    "Arithmetic operations",
    "Fractions and decimals",
    "Percentages",
    "Ratio and proportion",
    "Linear equations",
    "Systems of linear equations",
    "Quadratic equations",
    "Polynomial factorization",
    "Vieta formulas",
    "Polynomial remainder theorem",
    "Inequalities",
    "Absolute value equations",
    "Exponents and radicals",
    "Logarithms",
    "Sequences and series",
    "Coordinate geometry",
    "Trigonometric identities",
    "Limits",
    "Derivatives",
    "Basic integration",
]


def iter_topics_cycled(topic_items: List[str]) -> Iterable[str]:
    if not topic_items:
        raise ValueError("Topic list is empty. Add at least one topic in topic_list.py")

    index = 0
    while True:
        yield topic_items[index % len(topic_items)]
        index += 1


def load_topic_records_from_taxonomy(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return [{"chapter": "General Mathematics", "topic": topic} for topic in topics]

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    chapters = data.get("chapters", []) if isinstance(data, dict) else []
    records: List[Dict[str, str]] = []

    for chapter_item in chapters:
        if not isinstance(chapter_item, dict):
            continue

        chapter_name = str(chapter_item.get("chapter_name", "General Mathematics")).strip() or "General Mathematics"
        chapter_topics = chapter_item.get("topics", [])
        if not isinstance(chapter_topics, list):
            continue

        for topic_item in chapter_topics:
            if not isinstance(topic_item, dict):
                continue
            topic_name = str(topic_item.get("topic_name", "")).strip()
            if not topic_name:
                continue
            records.append({"chapter": chapter_name, "topic": topic_name})

    if records:
        return records

    return [{"chapter": "General Mathematics", "topic": topic} for topic in topics]


def iter_topic_records_cycled(topic_records: List[Dict[str, str]]) -> Iterable[Dict[str, str]]:
    if not topic_records:
        raise ValueError("No topic records found. Ensure taxonomy JSON contains chapters and topics.")

    index = 0
    while True:
        yield topic_records[index % len(topic_records)]
        index += 1
