"""
File: main.py
Author: Sean-Michael Riesterer
Description: Agentic AI workflow for gathering RSS feed based content into a newsfeed.
Version: v1.0.2
"""

import json
import logging
import os
import uuid
from datetime import UTC, datetime
from time import perf_counter

from openinference.instrumentation import using_session

# OpenTelemetry SDK Resources
from opentelemetry import trace as trace_api
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from agents import editor, researcher, writer
from config import (
    DATE_STR,
    DIGEST_DIR,
    DRAFT_DIR,
    ENABLE_DB,
    ENABLE_TRACING,
    LOG_DIR,
    LOG_FILE,
    LOG_LEVEL,
    MAX_REVISIONS,
    OTLP_ENDPOINT,
    console_format,
    json_formatter,
)
from db import create_table, fetch_existing_articles, insert_articles

# Local project modules
from ingest import ingest_rss_feeds
from publisher import write_newsletter


def setup():
    """Set up the prerequisites like logging, dirs for artifacts, and db"""
    # Setup logging
    os.makedirs(LOG_DIR / DATE_STR, exist_ok=True)
    file_handler = logging.FileHandler(LOG_FILE, mode="a")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(console_format))

    logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])

    # Setup current time
    current_utc_time = datetime.now(UTC)
    logging.info(f"Current UTC time {current_utc_time}")

    # Make sure output dirs exist
    for d in [DRAFT_DIR, DIGEST_DIR]:
        os.makedirs(d, exist_ok=True)

    if ENABLE_TRACING and OTLP_ENDPOINT:
        # Setup Otel tracing
        resource = Resource(attributes={"service.name": "ai-newstand"})
        tracer_provider = trace_sdk.TracerProvider(resource=resource)
        span_exporter = OTLPSpanExporter(endpoint=OTLP_ENDPOINT)
        tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
        trace_api.set_tracer_provider(tracer_provider)

    # Setup the database
    if ENABLE_DB:
        create_articles_table()


def create_articles_table():
    """Calls the db to create the articles table"""
    columns = {
        "id": "UUID PRIMARY KEY DEFAULT gen_random_uuid()",
        "source": "text",
        "title": "text",
        "summary": "text",
        "link": "text",
    }
    try:
        create_table("articles", columns)
        logging.info("Table: 'articles' created")
    except Exception as e:
        logging.error(f"Error creating articles table: {e}")
        raise


def filter_seen(articles: list[dict], existing: set[tuple[str, str]]) -> list[dict]:
    """Dedup the articles from those already in the database."""
    new_articles = [
        a for a in articles if (a.get("title"), a.get("link")) not in existing
    ]
    return new_articles


def main():
    """Main execution loop"""

    setup()

    id = str(uuid.uuid4())
    with using_session(session_id=id):
        start_main = perf_counter()
        ready_to_publish = False
        final = ""
        draft = ""
        feedback = ""
        revisions = 0
        articles = ingest_rss_feeds()
        if ENABLE_DB:
            existing = fetch_existing_articles("articles", articles)
            articles = filter_seen(articles, existing)
        curated_articles = researcher(articles)

        if not curated_articles:
            logging.error(
                f"Researcher returned no articles - or no valid JSON, got: {curated_articles}"
            )
            return
        logging.info(
            f"Passing {len(curated_articles)} articles to writer: {[a['source'] + ' - ' + a['title'][:40] for a in curated_articles]}"
        )

        if ENABLE_DB:
            insert_articles("articles", curated_articles)

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

        if final:
            write_newsletter(final)
        else:
            logging.error(f"Failed to write, no final or draft, final:{final}")
            exit(1)

        end_main = perf_counter()
        logging.info(f"Finished main execution in {end_main - start_main}s")
        exit(0)


if __name__ == "__main__":
    main()
