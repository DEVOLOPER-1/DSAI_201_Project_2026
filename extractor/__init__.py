MODEL = "qwen2.5-coder:latest"  # nuextract:latest , qwen2.5-coder:latest
MAX_CHARS = 7000  # truncation limit — stays within context window
KEEP_ALIVE = "10m"  # keep model hot between calls


SYSTEM_PROMPT = """\
You are an expert job posting data extractor with deep understanding of recruitment content in both English and Arabic.

Your task is to extract structured fields from raw job posting HTML. Be thorough and use inference where needed:
- If a field is not explicitly stated but can be reasonably inferred from context, infer it.
- If the job mentions "9am to 5pm, Monday to Friday" with no explicit type stated, infer job_type as "full-time".
- If the posting is clearly in Arabic, set language to "ar" even if not stated.
- If skills are mentioned anywhere in the text (requirements, responsibilities, tools), extract them all.
- If a company name appears in the HTML title, URL, or body, extract it even if not in a dedicated field.
- For location, infer from city names, landmarks, or district references in the text.
- For posted_at, infer from any relative date reference if an absolute date is unavailable.
    
Only use null when there is genuinely no information and nothing can be reasonably inferred.
Always respond with valid JSON only. No explanation. No markdown. No code fences.\
"""

JSON_SCHEMA = """\
{
    "title":           "string or null",
    "company":         "string or null",
    "location":        "string or null",
    "job_type":        "full-time | part-time | internship | remote | null",
    "salary":          "string or null",
    "language":        "en | ar | bilingual",
    "description":     "string or null",
    "requirements":    "string or null",
    "skills":          "array of strings or []",
    "posted_at":       "ISO date string or null",
    "application_url": "string or null",
    "extra_fields":    "object for anything else relevant or {}"
}\
"""
