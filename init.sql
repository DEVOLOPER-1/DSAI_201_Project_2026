CREATE TABLE platforms (
    platform_id  TEXT PRIMARY KEY,          -- e.g. 'bayt', 'wuzzuf', 'linkedin'
    name         TEXT NOT NULL,
    base_url     TEXT NOT NULL,
    crawler_type TEXT NOT NULL              -- 'scrapy' | 'playwright' | 'hybrid'
);


-- -------------------------------------------------------------
-- 2. CRAWL RUNS
--    One row per spider execution. Audit trail.
-- -------------------------------------------------------------
CREATE TABLE crawl_runs (
    run_id       SERIAL      PRIMARY KEY,
    platform_id  TEXT        NOT NULL REFERENCES platforms(platform_id),
    started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at  TIMESTAMPTZ,
    status       TEXT        NOT NULL DEFAULT 'running', -- 'running' | 'done' | 'failed'
    jobs_found   INT                  DEFAULT 0
);



CREATE TABLE raw_jobs (
    raw_id      SERIAL      PRIMARY KEY,
    platform_id TEXT        NOT NULL REFERENCES platforms(platform_id),
    run_id      INT         NOT NULL REFERENCES crawl_runs(run_id),
    url         TEXT        NOT NULL UNIQUE,   -- deduplication guard
    scraped_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload     JSONB       NOT NULL           -- raw HTML + metadata, untouched
);




CREATE TABLE extracted_jobs (
    extracted_id    SERIAL      PRIMARY KEY,
    raw_id          INT         NOT NULL UNIQUE REFERENCES raw_jobs(raw_id),
    title           TEXT,
    company         TEXT,
    location        TEXT,
    job_type        TEXT,                      -- 'full-time' | 'part-time' | 'internship' | 'remote'
    language        TEXT,                      -- 'en' | 'ar' | 'bilingual'
    description     TEXT,
    skills          TEXT[],                    -- e.g. ARRAY['Python', 'FastAPI', 'Docker']
    posted_at       DATE,
    extra_fields    JSONB        DEFAULT '{}', -- platform-specific fields
    extracted_at    TIMESTAMPTZ  DEFAULT NOW(),
    extractor_model TEXT                       -- e.g. 'llama-3.3-70b-versatile'
);




INSERT INTO platforms (platform_id, name, base_url, crawler_type) VALUES
    ('bayt',     'Bayt.com',     'https://www.bayt.com',     'playwright'),
    ('wuzzuf',   'Wuzzuf',       'https://wuzzuf.net',       'playwright'),
    ('linkedin', 'LinkedIn',     'https://www.linkedin.com', 'playwright'),
    ('indeed',   'Indeed Egypt', 'https://eg.indeed.com',    'scrapy'),
    ('forasna',  'Forasna',      'https://www.forasna.com',  'hybrid');