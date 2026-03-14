import re
import json
import ollama
from datetime import datetime, timezone
from extractor import JSON_SCHEMA, KEEP_ALIVE, MAX_CHARS, MODEL, SYSTEM_PROMPT

def _truncate(html: str) -> str:
    """Strip excess whitespace and cap at MAX_CHARS."""
    cleaned = re.sub(r"\s+", " ", html).strip()
    return cleaned[:MAX_CHARS]


def _strip_fences(text: str) -> str:
    """Remove markdown code fences if the model ignores the instruction."""
    return re.sub(r"```(?:json)?|```", "", text).strip()


def _build_user_prompt(raw_html: str) -> str:
    truncated = _truncate(raw_html)
    return (
        f"Extract from this job posting:\n"
        f"---\n{truncated}\n---\n\n"
        f"Return exactly this JSON structure:\n{JSON_SCHEMA}"
    )


def extract(raw_html: str) -> dict | None:
    """
    Pass raw HTML through the local LLM and return structured fields.
    Returns None on any failure — caller decides what to do.
    """
    user_prompt = _build_user_prompt(raw_html)

    try:
        response = ollama.chat(
            model=MODEL,
            keep_alive=KEEP_ALIVE,
            format="json",  # forces JSON output mode at the model level
            options={"temperature": 0.4},  # 0 ==> deterministic — no creativity needed
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        raw_text = response["message"]["content"]
        cleaned = _strip_fences(raw_text)
        parsed = json.loads(cleaned)

        # Stamp extraction metadata
        parsed["extracted_at"] = datetime.now(timezone.utc).isoformat()
        parsed["extractor_model"] = MODEL

        return parsed

    except json.JSONDecodeError as e:
        print(f"[extractor] JSON parse failed: {e}\nRaw output: {raw_text!r}")
        return None

    except Exception as e:
        print(f"[extractor] LLM call failed: {e}")
        return None

# if __name__ == "__main__":
#     sample_html = """
# "<div class=\"t-break\" data-jb-field=\"description\"> <p>Egypt Education Platform is looking for an experienced and passionate PYP Librarian Teacher to join our team at GEMS International School Cairo for next academic year commencing from August 2026.<br> The successful applicants will have the following: A passion for providing outstanding teaching and driven to provide education at an exceptional level.<br> Teachers enjoy an outstanding school environment in which to deliver a dynamic and creative curriculum to motivated students.<br> Bachelor's degree in relevant field.<br> Teachers are expected to have a current license/certification in their home country with a minimum of 3 years full-time teaching experience.<br> Teaching certificate.<br> PYP training is preferred PYP experience is preferred.<br> Aspiration to work in a world class school with real prospects for enhancing their career.<br> The safeguarding of our students is at the core of all that we do.<br> all appointments are conditional on: Acceptable police checks (or equivalent) from the country of origin and from all counties in which you have worked.<br> Appropriate references from your current and previous employer, corroborated by personal phone calls made to each.<br></p> </div>"}
# """
#     result = extract(sample_html)
#
#     if result:
#         print(json.dumps(result, indent=2, ensure_ascii=False))
#     else:
#         print("Extraction failed.")
