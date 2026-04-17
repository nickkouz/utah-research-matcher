from __future__ import annotations

import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "scraped_faculty.json"
SEED_URLS = [
    "https://www.cs.utah.edu/people/faculty/",
]


def scrape_seed_page(url: str) -> list[dict]:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n", strip=True)
    return [
        {
            "source_url": url,
            "raw_text": text[:10000],
        }
    ]


def run() -> list[dict]:
    rows = []
    for url in SEED_URLS:
        rows.extend(scrape_seed_page(url))
    OUTPUT_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    return rows


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
