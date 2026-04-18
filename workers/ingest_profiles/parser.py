from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from workers.common.text import normalize_whitespace, slugify


PROFILE_SECTION_HINTS = ("biography", "research", "overview", "summary", "interests", "about")


@dataclass
class ParsedStaffProfile:
    id: str
    profile_slug: str
    name: str
    title: str | None
    email: str | None
    profile_url: str
    bio: str | None
    primary_school: str | None
    school_affiliations: list[str]
    department: str | None


def parse_profile_html(html: str, profile_url: str) -> ParsedStaffProfile | None:
    soup = BeautifulSoup(html, "html.parser")
    name = _extract_name(soup)
    if not name:
        return None
    profile_slug = _profile_slug(profile_url)
    title = _extract_title(soup)
    email = _extract_email(soup)
    bio = _extract_bio(soup)
    schools = _extract_school_affiliations(soup)
    department = _extract_department(soup)
    return ParsedStaffProfile(
        id=slugify(profile_slug) or slugify(name),
        profile_slug=profile_slug,
        name=name,
        title=title,
        email=email,
        profile_url=profile_url,
        bio=bio,
        primary_school=schools[0] if schools else None,
        school_affiliations=schools,
        department=department,
    )


def _extract_name(soup: BeautifulSoup) -> str | None:
    heading = soup.find(["h1", "h2"])
    if heading:
        candidate = normalize_whitespace(heading.get_text(" ", strip=True))
        if candidate and len(candidate) <= 120:
            return candidate
    if soup.title:
        title_text = normalize_whitespace(soup.title.get_text(" ", strip=True))
        if "|" in title_text:
            candidate = title_text.split("|", 1)[0].strip()
            if candidate and len(candidate) <= 120:
                return candidate
        return title_text
    return None


def _extract_title(soup: BeautifulSoup) -> str | None:
    selectors = [
        "[class*=title]",
        "[class*=position]",
        "[class*=rank]",
        "[class*=appointment]",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            text = normalize_whitespace(node.get_text(" ", strip=True))
            if text and len(text) <= 120:
                return text
    return None


def _extract_email(soup: BeautifulSoup) -> str | None:
    link = soup.select_one("a[href^='mailto:']")
    if link:
        return normalize_whitespace(link.get("href", "").replace("mailto:", ""))
    return None


def _extract_bio(soup: BeautifulSoup) -> str | None:
    sections = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = normalize_whitespace(heading.get_text(" ", strip=True)).lower()
        if any(token in heading_text for token in PROFILE_SECTION_HINTS):
            paragraphs = []
            for sibling in heading.find_all_next(limit=10):
                if sibling.name in {"h2", "h3", "h4"} and sibling is not heading:
                    break
                if sibling.name == "p":
                    paragraphs.append(normalize_whitespace(sibling.get_text(" ", strip=True)))
            if paragraphs:
                sections.append(" ".join(paragraphs))
    if sections:
        return max(sections, key=len)

    paragraphs = [
        normalize_whitespace(node.get_text(" ", strip=True))
        for node in soup.find_all("p")
        if normalize_whitespace(node.get_text(" ", strip=True))
    ]
    if not paragraphs:
        return None
    return max(paragraphs, key=len)


def _extract_school_affiliations(soup: BeautifulSoup) -> list[str]:
    text_nodes = soup.get_text("\n", strip=True).splitlines()
    schools = []
    for line in text_nodes:
        cleaned = normalize_whitespace(line)
        if not cleaned:
            continue
        if "College of " in cleaned or "School of " in cleaned:
            if cleaned not in schools:
                schools.append(cleaned)
    return schools[:6]


def _extract_department(soup: BeautifulSoup) -> str | None:
    text_nodes = soup.get_text("\n", strip=True).splitlines()
    for line in text_nodes:
        cleaned = normalize_whitespace(line)
        if "Department of " in cleaned or cleaned.endswith(" Department") or "School of Computing" in cleaned:
            return cleaned
    return None


def _profile_slug(profile_url: str) -> str:
    path = urlparse(profile_url).path.strip("/")
    return path.split("/")[-1]
