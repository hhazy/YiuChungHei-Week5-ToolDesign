### Sentinel Text Analysis Demo

This mini project provides a **tool-enabled text analysis pipeline** built around DeepSeek. It generates a synthetic news-style article, normalises its datetime into Hong Kong Time (HKT, ISO 8601), and computes simple text statistics, returning a JSON‑serialisable result.

### Realistic use case

You’re building a small “news hygiene” feature for a student app:
- Generate (or fetch) a few short news items
- **Normalise dates** so they can be sorted/filtered reliably
- Compute quick **text metrics** (sentence/character counts) to detect unusually short/long items and flag them for review

### What the tool does

- **Tools in `tool.py`**
  - **`count_sentence(text)`**: Counts sentences by looking for `.`, `!`, or `?` followed by whitespace or end‑of‑string.
  - **`count_words(text)`**: Counts words using a simple pattern for alphanumeric tokens/apostrophes.
  - **`parse_date(date_time_str)`**: Parses a datetime string that includes a timezone (e.g. `2026-02-27T14:30:00+02:00`) and converts it to **HKT** (`Asia/Hong_Kong`) in ISO 8601 format (e.g. `2026-02-27T21:30:00+08:00`).
- **Demo workflow**
  - **`demo.py`** calls the DeepSeek chat API to generate **one single-paragraph news article (~500–600 words)**.
  - The **first word of the paragraph** is constrained to be a datetime with timezone; `demo.py` extracts this, passes it to `parse_date()`, and then runs `count_sentence()` and `count_words()` on the full paragraph.
  - The final output is a dict like:
    - `{"results": [{"datetime_hkt": "YYYY-MM-DDThh:mm:ss+08:00", "sentences": int, "words": int, "article": "string"}]}`.

### How to run the demo

- **1. Install dependencies**
  - Python 3.10+ is recommended.
  - Install packages (in your virtualenv or environment):
    - `pip install openai python-dotenv`
- **2. Configure DeepSeek**
  - Create a `.env` file in the project root (same folder as `tool.py`) with:
    - `DEEPSEEK_API_KEY=...`
    - `DEEPSEEK_API_BASE=https://api.deepseek.com`
    - `DEEPSEEK_MODEL=deepseek-chat`
- **3. Run the demo script**
  - From the project root:
    - `python demo.py`
  - The script calls DeepSeek, then uses the tools from `tool.py`, and pretty‑prints the JSON result to the console.
  - If DeepSeek fails or returns unexpected JSON, or the output schema is wrong, `demo.py` prints an error to stderr and exits with a non‑zero code.

### Design decisions and limitations

- **Design decisions**
  - **Beginner‑friendly structure**: `tool.py` is a small collection of pure functions with type hints and docstrings; all API interaction lives in `demo.py`.
  - **Separation of concerns**: DeepSeek prompting/parsing is kept in the demo script, while `tool.py` focuses purely on text and datetime utilities.
  - **Robust but simple parsing**: DeepSeek responses are expected to be JSON; `demo.py` has a small fallback that extracts the first JSON object if extra text is present.
  - **Clear error propagation**: Low‑level errors raise exceptions; `demo.py` catches them, reports a readable error, and exits non‑zero so callers can detect failure.
- **Limitations**
  - **Model response assumptions**: The code assumes DeepSeek returns well‑formed JSON with an `articles` list and an `article` string; if the structure changes, parsing may fail.
  - **Datetime parsing**: `parse_date()` relies on ISO 8601 offsets or a small set of explicit patterns; unusual datetime formats may raise errors.
  - **Sentence and word counting**: Both rely on simple regexes; edge cases like abbreviations (`U.S.`), decimals (`3.14`), or emojis may affect counts.
  - **No tests or logging**: To keep things minimal and follow the project rules, there are no automated tests and no logging framework—only basic exceptions and console output in `demo.py`.
