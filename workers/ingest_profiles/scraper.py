from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from workers.common.bootstrap import ensure_api_path


ensure_api_path()

from app.core.config import settings  # noqa: E402


PROFILE_HOST = urlparse(settings.profiles_base_url).netloc
PROFILE_PATH_RE = re.compile(r"^/u[^/?#]+/?$")


def fetch_profile_pages(limit: int | None = None) -> list[tuple[str, str]]:
    urls = discover_profile_links(limit=limit)
    pages = []
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for url in urls:
            try:
                response = client.get(url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            pages.append((url, response.text))
    return pages


def discover_profile_links(limit: int | None = None) -> list[str]:
    sitemap_links = _discover_from_sitemaps(limit=limit)
    if sitemap_links:
        return sitemap_links

    discovered: set[str] = set()
    queue = list(settings.profiles_seed_urls)
    visited: set[str] = set()

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        while queue:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            try:
                response = client.get(url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                absolute = urljoin(url, link["href"])
                parsed = urlparse(absolute)
                if parsed.netloc != PROFILE_HOST:
                    continue
                cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                if PROFILE_PATH_RE.match(parsed.path):
                    discovered.add(cleaned)
                    if limit and len(discovered) >= limit:
                        return sorted(discovered)
                elif cleaned not in visited and cleaned not in queue and len(visited) < 50:
                    queue.append(cleaned)

    return sorted(discovered)


def _discover_from_sitemaps(limit: int | None = None) -> list[str]:
    candidate_sitemaps = [
        f"{settings.profiles_base_url.rstrip('/')}/sitemap.xml",
        f"{settings.profiles_base_url.rstrip('/')}/sitemap_index.xml",
    ]
    discovered: set[str] = set()
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for sitemap_url in candidate_sitemaps:
            try:
                response = client.get(sitemap_url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            soup = BeautifulSoup(response.text, "xml")
            for loc in soup.find_all("loc"):
                text = (loc.text or "").strip()
                parsed = urlparse(text)
                if parsed.netloc != PROFILE_HOST:
                    continue
                cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
                if PROFILE_PATH_RE.match(parsed.path):
                    discovered.add(cleaned)
                    if limit and len(discovered) >= limit:
                        return sorted(discovered)
    return sorted(discovered)
