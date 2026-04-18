from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\\-]+")

SECTOR_HINTS = {
    "Healthcare Technology": ["health", "clinical", "medical", "patient", "hospital", "biomedical"],
    "Energy": ["energy", "power", "grid", "battery", "sustainability"],
    "Financial Technology": ["finance", "bank", "trading", "risk", "market"],
    "Robotics": ["robot", "robotics", "autonomy", "manipulation"],
    "Education Technology": ["education", "learning", "student", "instruction"],
}

TECHNICAL_HINTS = {
    "machine learning": ["machine learning", "deep learning", "representation learning"],
    "natural language processing": ["language", "text", "nlp", "linguistic"],
    "computer vision": ["vision", "image", "video", "visual"],
    "systems": ["systems", "distributed", "architecture", "infrastructure"],
    "security": ["security", "privacy", "adversarial", "cryptography"],
    "robotics": ["robotics", "autonomy", "control"],
}


def extract_keywords(text: str, limit: int = 12) -> list[str]:
    tokens = []
    for token in TOKEN_RE.findall(text):
        lowered = token.lower()
        if len(lowered) < 4:
            continue
        if lowered not in tokens:
            tokens.append(lowered)
    return tokens[:limit]


def infer_sector_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = [sector for sector, hints in SECTOR_HINTS.items() if any(hint in lowered for hint in hints)]
    return tags[:4]


def infer_technical_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = [tag for tag, hints in TECHNICAL_HINTS.items() if any(hint in lowered for hint in hints)]
    return tags[:6]

