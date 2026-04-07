"""
File: ingest.py
Author: Sean-Michael Riesterer
Description: Functions to gather articles from RSS Feeds and parse content with bs4
"""

import logging
import requests
from requests import RequestException, Response
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta, UTC
from time import mktime, perf_counter
from config import TIMEFRAME_HOURS
import json


def fetch_article(url: str) -> str | None:
    """Requests a page from URL via HTTP"""

    logging.info(f"Fetching URL: {url}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
    except RequestException as e:
        logging.error(f"Caught Request Exception {e}")
        return None

    if response.status_code == 200 and "text/html" in content_type:
        return parse_article(response)
    else:
        return None


def parse_article(response: Response) -> str | None:
    """Parses page to extract text content."""

    soup = BeautifulSoup(response.content, "html.parser")
    noise_tags = [
        "nav",
        "footer",
        "header",
        "aside",
        "script",
        "meta",
        "style",
        "form",
        "svg",
        "noscript",
        "iframe",
        "button",
    ]

    noise_selectors = [
        '[role="navigation"]',
        '[role="complementary"]',
        '[role="banner"]',
        ".comments",
        ".comment-section",
        "#comments",
        ".sidebar",
        "#sidebar",
        ".social-share",
        ".share-buttons",
        ".sharing",
        ".related-posts",
        ".recommended",
        ".read-next",
        ".newsletter-signup",
        ".subscribe",
        ".cookie-banner",
        ".cookie-consent",
        ".author-bio",
        ".author-card",
        ".table-of-contents",
        ".toc",
        ".breadcrumb",
        ".breadcrumbs",
        ".pagination",
        ".ad",
        ".advertisement",
        ".sponsored",
    ]

    for selector in noise_selectors:
        for el in soup.select(selector):
            el.decompose()

    for tag_noise in soup.find_all(noise_tags):
        tag_noise.decompose()

    content = soup.find("article") or soup.find("main") or soup.find("body")

    if content:
        text = content.get_text(separator="\n", strip=True)
        if len(text) < 200:
            return None
        logging.info(f"Extracted {len(text)} chars from content.")
        return text


def parse_entry(name: str, url: str, entry: dict):
    """Parse a single entry dict if it's recent enough and return the dict"""
    # Some feeds use published, others updated, we check both regardless.
    date = entry.get("published_parsed", None) or entry.get("updated_parsed", None)
    if date:
        # Get a datetime object from the date we parsed.
        timestamp = mktime(date)  # type: ignore[arg-type]
        published_datetime_obj = datetime.fromtimestamp(timestamp, UTC)

        # Get a datetime object for the current UTC time
        current_utc_time = datetime.now(UTC)

        # If the published time is after current time minus the timeframe window, save it
        if published_datetime_obj > current_utc_time - timedelta(hours=TIMEFRAME_HOURS):
            # Add our source name and url to the dict
            entry.update({"source_feed": name, "source_url": url})
            return entry


def ingest_rss_feeds() -> list[dict]:
    """Parse RSS feeds and return list of FeedParserDict"""
    feeds = None
    with open("feeds.json", "r") as json_file:
        feeds = json.load(json_file)
    results = []

    start = perf_counter()
    for name, url in feeds.items():
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                logging.warning(f"No entries from feed: {name} ({url})")
            for entry in feed.entries:
                parsed_entry = parse_entry(name, url, entry)
                if parsed_entry:
                    results.append(parsed_entry)
            new_entries = [e for e in results if e.get("source_feed") == name]
            logging.debug(f"Got {len(new_entries)} recent entries for {name}")

        except Exception as e:
            logging.error(f"Caught exception parsing url {url} {e}")

    end = perf_counter()
    logging.debug(f"RSS parser finished in {end - start}s")
    return results
