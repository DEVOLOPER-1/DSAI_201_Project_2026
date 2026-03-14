import os
import psycopg2
import psycopg2.extras  # for execute_values and Json adapter

from datetime import datetime, timezone
from dotenv import load_dotenv

# crawler/pipelines.py (top)
import sys
from pathlib import Path

# __file__ is .../project_root/crawler/pipelines.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # goes up one level to project root
sys.path.insert(0, str(PROJECT_ROOT))

# now regular import works
from extractor.nlp_extractor import extract
import gc

load_dotenv()


# ─────────────────────────────────────────────────────────────
# POSTGRES PIPELINE
# Responsibilities:
#   open_spider  → open DB connection, create crawl_run row
#   process_item → INSERT raw_jobs → call extractor → INSERT extracted_jobs
#   close_spider → UPDATE crawl_run to done/failed, close connection
# ─────────────────────────────────────────────────────────────


class PostgresPipeline:
    # ── Lifecycle ────────────────────────────────────────────
    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", 5432),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PW"),
        )
        self.conn.autocommit = False  # explicit transaction control
        self.cursor = self.conn.cursor()
        self.jobs_inserted = 0  # tracks raw_jobs inserted this run

        platform_id = getattr(spider, "platform_id", spider.name)

        # Open the crawl_run row — status starts as 'running'
        self.cursor.execute(
            """
            INSERT INTO crawl_runs (platform_id, started_at, status)
            VALUES (%s, %s, 'running')
            RETURNING run_id
            """,
            (platform_id, datetime.now(timezone.utc)),
        )
        self.run_id = self.cursor.fetchone()[0]
        self.platform_id = platform_id
        self.conn.commit()

        spider.logger.info(
            f"[PostgresPipeline] crawl_run #{self.run_id} opened "
            f"for platform '{self.platform_id}'"
        )

    def close_spider(self, spider):
        try:
            self.cursor.execute(
                """
                UPDATE crawl_runs
                SET    status       = 'done',
                       finished_at  = %s,
                       jobs_found   = %s
                WHERE  run_id       = %s
                """,
                (datetime.now(timezone.utc), self.jobs_inserted, self.run_id),
            )
            self.conn.commit()
            spider.logger.info(
                f"[PostgresPipeline] crawl_run #{self.run_id} closed — "
                f"{self.jobs_inserted} raw jobs inserted"
            )

        except Exception as e:
            self.conn.rollback()
            self.cursor.execute(
                "UPDATE crawl_runs SET status='failed', finished_at=%s WHERE run_id=%s",
                (datetime.now(timezone.utc), self.run_id),
            )
            self.conn.commit()
            spider.logger.error(f"[PostgresPipeline] close_spider error: {e}")

        finally:
            self.cursor.close()
            self.conn.close()
            gc.collect()

    def process_item(self, item, spider):

        raw_id = self._insert_raw_job(item, spider)

        if raw_id is None:
            return item

        # ── Step 2: LLM extraction ───────────────────────────
        raw_html = item.get("raw_html_payload", "")
        fields = extract(raw_html)

        if fields is None:
            spider.logger.warning(
                f"[PostgresPipeline] extraction failed for raw_id={raw_id} "
                f"url={item.get('url')}"
            )
            return item  # raw job is saved — extraction can be retried later

        # ── Step 3: extracted_jobs ───────────────────────────
        self._insert_extracted_job(raw_id, fields, spider)

        return item  # return item so other pipelines in the chain can use it

    # ── Private helpers ───────────────────────────────────────
    def _insert_raw_job(self, item, spider) -> int | None:
        """
        Insert one row into raw_jobs.
        Returns the raw_id if inserted, None if the URL already existed.
        """
        payload = {
            "job_title": item.get("job_title"),
            "raw_html_payload": item.get("raw_html_payload"),
        }

        try:
            self.cursor.execute(
                """
                INSERT INTO raw_jobs (platform_id, run_id, url, payload)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING
                RETURNING raw_id
                """,
                (
                    self.platform_id,
                    self.run_id,
                    item["url"],
                    psycopg2.extras.Json(payload),  # serialises dict → JSONB
                ),
            )
            self.conn.commit()

            row = self.cursor.fetchone()
            if row is None:
                # ON CONFLICT DO NOTHING fired — URL already in DB
                spider.logger.debug(
                    f"[PostgresPipeline] duplicate skipped: {item['url']}"
                )
                return None

            self.jobs_inserted += 1
            return row[0]  # raw_id of the newly inserted row

        except Exception as e:
            self.conn.rollback()
            spider.logger.error(
                f"[PostgresPipeline] raw_jobs insert failed: {e} | url={item.get('url')}"
            )
            return None

    def _insert_extracted_job(self, raw_id: int, fields: dict, spider) -> None:
        """
        Insert LLM-extracted fields into extracted_jobs.
        ON CONFLICT DO UPDATE allows re-extraction to overwrite stale rows.
        """
        # skills comes from the LLM as a Python list — cast to Postgres array
        skills = fields.get("skills") or []
        if not isinstance(skills, list):
            skills = []

        # posted_at may be an ISO string or None — keep as string, PG casts to DATE
        posted_at = fields.get("posted_at")

        try:
            self.cursor.execute(
                """
                INSERT INTO extracted_jobs (
                    raw_id, title, company, location, job_type,
                    language, description, requirements, skills,
                    posted_at, extra_fields, extracted_at, extractor_model
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s
                )
                ON CONFLICT (raw_id) DO UPDATE SET
                    title           = EXCLUDED.title,
                    company         = EXCLUDED.company,
                    location        = EXCLUDED.location,
                    job_type        = EXCLUDED.job_type,
                    language        = EXCLUDED.language,
                    description     = EXCLUDED.description,
                    requirements    = EXCLUDED.requirements,
                    skills          = EXCLUDED.skills,
                    posted_at       = EXCLUDED.posted_at,
                    extra_fields    = EXCLUDED.extra_fields,
                    extracted_at    = EXCLUDED.extracted_at,
                    extractor_model = EXCLUDED.extractor_model
                """,
                (
                    raw_id,
                    fields.get("title"),
                    fields.get("company"),
                    fields.get("location"),
                    fields.get("job_type"),
                    fields.get("language"),
                    fields.get("description"),
                    fields.get("requirements"),
                    skills,  # TEXT[]
                    posted_at,
                    psycopg2.extras.Json(fields.get("extra_fields") or {}),
                    fields.get("extracted_at"),
                    fields.get("extractor_model"),
                ),
            )
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            spider.logger.error(
                f"[PostgresPipeline] extracted_jobs insert failed: {e} | raw_id={raw_id}"
            )
