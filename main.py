"""
File: main.py
Author: Sean-Michael Riesterer
Description: Agentic AI workflow for gathering RSS feed based content into a newsfeed.
Version: v1.0.0
"""

import feedparser
import logging
from datetime import datetime, timedelta, UTC
from time import mktime, perf_counter
import json
import re
from ollama import chat, ChatResponse
from zoneinfo import ZoneInfo
import boto3
from pathlib import Path
from botocore.exceptions import ClientError
import os
import requests
from requests import Response, RequestException
from bs4 import BeautifulSoup
import concurrent.futures
from pythonjsonlogger.json import JsonFormatter

from prompts import (
    RESEARCHER_SYSTEM_PROMPT,
    RESEARCHER_USER_PROMPT,
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
    WRITER_SYSTEM_PROMPT,
    WRITER_USER_PROMPT,
    EDITOR_SYSTEM_PROMPT,
    EDITOR_USER_PROMPT,
)

# Boolean to control wether or not the generated digest is 'published' by uploading to s3
PUBLISH = False

DATE_STR = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")

BASE_PATH = Path(__file__).parent
DRAFT_DIR = BASE_PATH / "drafts" / DATE_STR
DIGEST_DIR = BASE_PATH / "digests"
LOG_DIR = BASE_PATH / "logs"
LOG_FILE = (
    LOG_DIR / DATE_STR / f"main-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
)

RESEARCHER_MODEL = "gpt-oss:20b"
WRITER_MODEL = "gpt-oss:20b"
EDITOR_MODEL = "gpt-oss:20b"
NUM_CTX = 32768
MAX_REVISIONS = 3
TIMEFRAME_HOURS = 24
INTERESTS = [
    "AI",
    "ML",
    "MLOps",
    "LLMOps",
    "Platform Engineering",
    "AI Engineering",
    "DevOps",
    "Kubernetes",
    "NVIDIA",
    "LangChain",
    "Agents",
    "Anthropic",
    "Claude Code",
    "Codex",
    "AMD",
    "Intel",
    "Hugging Face",
    "PyTorch",
    "Ollama",
    "vLLM",
    "MCP",
    "RAG",
    "vector databases",
    "OpenAI",
    "Gemini",
    "Mistral",
    "Qwen",
    "Terraform",
    "ArgoCD",
    "GitOps",
]

S3_CONTENT_BUCKET = os.getenv("S3_CONTENT_BUCKET", "smr-webdev-content")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")


console_format = "%(asctime)s - %(levelname)s - %(message)s"
json_formatter = JsonFormatter("%(asctime)s %(levelname)s %(message)s")

LOG_LEVEL = logging.INFO

os.makedirs(LOG_DIR / DATE_STR, exist_ok=True)
file_handler = logging.FileHandler(LOG_FILE, mode="a")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(json_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(logging.Formatter(console_format))

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

current_utc_time = datetime.now(UTC)
logging.info(f"Current UTC time {current_utc_time}")


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


def chat_with_ollama(
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    think: bool = False,
    options=None,
    tools=None,
) -> ChatResponse:
    """Sends a chat to a model with a prompt"""
    message = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    start = perf_counter()

    response = chat(
        model=model_name,
        messages=message,
        think=think,
        options=options or {"num_ctx": NUM_CTX},
        tools=tools,
    )

    finish = perf_counter()
    logging.debug(f"Response from Ollama: {response}")
    logging.debug(f"Chat finished in {finish - start}s")
    return response


def ingest_rss_feeds() -> dict:
    """Parse RSS feeds and return dictionary of information"""
    """TODO: Add some try/except timeout/rate limit handling"""
    feeds = None
    with open("feeds.json", "r") as json_file:
        feeds = json.load(json_file)
    results = {}

    start = perf_counter()
    for name, url in feeds.items():
        results[name] = []
        feed = feedparser.parse(url)
        for entry in feed.entries:
            date = entry.get("published_parsed", None) or entry.get(
                "updated_parsed", None
            )
            if date:
                timestamp = mktime(date)  # type: ignore[arg-type]
                datetime_obj = datetime.fromtimestamp(timestamp, UTC)
                if datetime_obj > current_utc_time - timedelta(hours=TIMEFRAME_HOURS):
                    results[name].append(entry)
        if results.get(name, []):
            logging.debug(f"Got {len(results.get(name, ''))} recent entries for {name}")
    end = perf_counter()
    logging.debug(f"RSS parser finished in {end - start}s")
    return results


def build_researcher_prompt(interests: list[str], articles: str) -> str:
    prompt = f"""You are a researcher of news stories for an AI / ML Ops professional interested in the following topics: {interests}. 
    Specifically focus on new technology or product releases, workflows, techniques, or otherwise 'technical' content rather than social or political.
    Given a list of articles in the following format:
            "source": source,
            "title": entry.title,
            "summary": entry.summary,
            "link": entry.link
    
    1. Select no more than 10 articles that best match the interest topics and criteria.
        - Try to use a mixture of sources to capture a variety of topics.
        - Prioritize content from: Hugging Face Blog, MLOps Community, CNCF Blog when available
    2. Gather the UNIQUE links for each article 
    3. Return ONLY a JSON array of selected article links, nothing else. Example format:
["https://...", "https://..."]
    
    ARTICLES:
    {articles}
    """
    return prompt


def summarize_article(article: dict):
    body = {re.sub(r"<[^>]+>", "", article.get("content", "NO CONTENT"))}
    response = chat_with_ollama(
        RESEARCHER_MODEL,
        SUMMARY_SYSTEM_PROMPT.template,
        SUMMARY_USER_PROMPT.render(article=body),
        think=False,
    )

    summary = response.message.content
    logging.debug(f"Summary of {article.get('title')}\n\t{summary}")

    summarized = {
        "source": article.get("source", "NO SOURCE"),
        "title": article.get("title", "NO TITLE"),
        "summary": summary,
        "link": article.get("link", "NO LINK"),
    }
    return summarized


def researcher(raw_articles: dict[str, list]) -> list[dict] | None:
    """Refine article results into best candidates"""
    logging.info(
        f"Ingested {sum(len(v) for v in raw_articles.values())} total articles from {len(raw_articles)} feeds"
    )
    trimmed = [
        {
            "source": source,
            "title": entry.get("title", "NO TITLE"),
            "summary": entry.get("summary", "NO SUMMARY"),
            "content": (
                entry.get("content", [{}])[0].get("value", "")
                or entry.get("summary", "NO CONTENT")
            )[:3000],
            "link": entry.get("link", "NO LINK"),
        }
        for source, entries in raw_articles.items()
        for entry in entries
    ]

    thin_articles = [
        a
        for a in trimmed
        if (len(a.get("content", "")) < 200 or "NO CONTENT" in a.get("content", ""))
    ]

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_article = {
            executor.submit(fetch_article, a.get("link", "")): a for a in thin_articles
        }

        for future in concurrent.futures.as_completed(future_to_article):
            try:
                a = future_to_article[future]
                logging.info(
                    f"RSS got no content for '{a.get('title', 'unknown')}', fetching article"
                )
                a["content"] = future.result() or "NO CONTENT"
                logging.debug(f"Fetched content length: {len(a['content'])}")
                if a["content"] == "NO CONTENT":
                    logging.info(
                        f"Could not fetch article content for '{a.get('title', 'unknown')}"
                    )
            except RequestException as e:
                logging.error(f"Exception caught in task future: {e}")
            except Exception as e:
                logging.error(f"Exception caught in task future: {e}")

    trimmed_for_curation = [
        {k: a[k] for k in ("source", "title", "summary", "link")} for a in trimmed
    ]
    researcher_prompt = RESEARCHER_USER_PROMPT.render(
        interests=INTERESTS, articles=json.dumps(trimmed_for_curation)
    )
    response = ""

    try:
        response = chat_with_ollama(
            RESEARCHER_MODEL,
            RESEARCHER_SYSTEM_PROMPT.template,
            researcher_prompt,
            think=False,
        )
    except Exception as e:
        logging.error(f"Caught Exception: {e}")
        return None

    try:
        curated_links = list(set(json.loads(response.message.content or "[]")))
        logging.info(f"Researcher selected {len(curated_links)} unique links")
        logging.debug(f"researcher links: {curated_links}")
        curated_articles = [a for a in trimmed if a.get("link") in curated_links]
        logging.debug(f"curated_articles: {curated_articles}")
        logging.info(f"Researcher curated {len(curated_articles)} articles")

        summarized_articles = [summarize_article(a) for a in curated_articles]
        logging.info(f"Researcher summarized {len(summarized_articles)} articles")
        logging.info(f"Article sources: {[a['source'] for a in summarized_articles]}")
        return summarized_articles
    except Exception as e:
        logging.error(f"Caught exception: {e}")
        return None


def writer(
    articles: list[dict[str, str]], previous_draft: str | None, feedback: str | None
) -> str | None:
    """Take curated articles and generate a Newsletter.MD"""
    logging.info(f"Writer recieved {len(articles)} articles.")
    newsletter = ""
    if feedback is None:
        feedback = ""

    response = chat_with_ollama(
        WRITER_MODEL,
        WRITER_SYSTEM_PROMPT.template,
        WRITER_USER_PROMPT.render(
            date_str=DATE_STR,
            articles=articles,
            feedback=feedback,
            draft=previous_draft,
        ),
        think=False,
    )
    newsletter = response.message.content
    logging.info("Writer generated draft.")
    return newsletter


def editor(draft: str) -> str | None:
    """Take draft newsletter and provide feedback, if no edits, return LGTM!"""

    response = chat_with_ollama(
        EDITOR_MODEL,
        EDITOR_SYSTEM_PROMPT.template,
        EDITOR_USER_PROMPT.render(date_str=DATE_STR, draft=draft),
        think=False,
    )
    feedback = response.message.content
    logging.info("Editor generated feedback.")
    return feedback


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client("s3", region_name=AWS_REGION)
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True


def extract_title(newsletter_md: str) -> str:
    """Extract the H1 title from the newsletter markdown."""
    for line in newsletter_md.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return "AI Newsletter"


def make_slug(title: str) -> str:
    """Convert a title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug).strip("-")
    return slug


def write_newsletter(final: str) -> None:
    """
    Add frontmatter, save locally, and upload to S3.
    """

    title = extract_title(final)
    slug = make_slug(title)

    frontmatter = f"""---
title: "{title}"
date: {DATE_STR}
---
"""
    full_content = frontmatter + final
    filename = DIGEST_DIR / f"{slug}.md"
    chars_written = 0

    with open(filename, "w") as file:
        try:
            chars_written = file.write(full_content)
            if chars_written < 1:
                logging.error(f"Wrote an empty file to {filename}.")
                return
        except Exception as e:
            logging.error(f"Caught exception writing digest: {e}")
            return

    if PUBLISH:
        object_name = f"digests/{filename.name}"
        uploaded = upload_file(filename, S3_CONTENT_BUCKET, object_name)
        if uploaded:
            logging.info(f"Uploaded {filename} to s3://{S3_CONTENT_BUCKET}")
        else:
            logging.error(f"Failed to upload {filename} to s3://{S3_CONTENT_BUCKET}")


def main():
    """Main execution loop"""

    for d in [DRAFT_DIR, DIGEST_DIR]:
        os.makedirs(d, exist_ok=True)

    start_main = perf_counter()
    ready_to_publish = False
    final = ""
    draft = ""
    feedback = ""
    revisions = 0
    raw_articles = ingest_rss_feeds()
    curated_articles = researcher(raw_articles)

    if not curated_articles:
        logging.error(
            f"Researcher returned no articles - or no valid JSON, got: {curated_articles}"
        )
        return
    logging.info(
        f"Passing {len(curated_articles)} articles to writer: {[a['source'] + ' - ' + a['title'][:40] for a in curated_articles]}"
    )

    while not ready_to_publish and revisions < MAX_REVISIONS:
        start_revision = perf_counter()
        draft = writer(curated_articles, draft, feedback)
        if not draft:
            revisions += 1
            continue

        draft_filename = DRAFT_DIR / f"draft-{revisions}"
        with open(draft_filename, "w") as draft_file:
            draft_file.write(draft)

        feedback = editor(draft)
        if not feedback:
            revisions += 1
            continue

        edit_filename = DRAFT_DIR / f"edits-{revisions}"
        with open(edit_filename, "w") as edit_file:
            edit_file.write(feedback)

        if feedback.strip() == "LGTM":
            ready_to_publish = True
            final = draft
            end_revision = perf_counter()
            logging.info(
                f"Editorial loop {revisions} finished in {end_revision - start_revision}s"
            )
            logging.info("Editor approved the draft, print it!")

        revisions += 1
        end_revision = perf_counter()
        logging.info(
            f"Editorial loop {revisions} finished in {end_revision - start_revision}s"
        )

    final = final or draft
    logging.info(f"Agent loop finished in {revisions} iterations.")

    metadata = f"""

---
*Researcher: {RESEARCHER_MODEL} • Writer: {WRITER_MODEL} • Editor: {EDITOR_MODEL}*
"""
    if final:
        final_copy = final + metadata
        write_newsletter(final_copy)

    end_main = perf_counter()
    logging.info(f"Finished main execution in {end_main - start_main}s")


if __name__ == "__main__":
    main()
