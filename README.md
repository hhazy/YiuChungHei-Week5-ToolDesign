### Sentinel Text Analysis Demo

This mini project provides a **tool-enabled text analysis pipeline** with **one agent** and local tools. The pipeline uses a single DeepSeek-backed agent to generate a synthetic news-style article; then `tool.py` is used to normalise its datetime into Hong Kong Time (HKT, ISO 8601) and to compute simple text statistics, returning a JSON‑serialisable result.

### Realistic use case

You’re building a small “news hygiene” feature for a student app:
- Generate (or fetch) a few short news items
- **Normalise dates** so they can be sorted/filtered reliably
- Compute quick **text metrics** (sentence/character counts) to detect unusually short/long items and flag them for review

### What the tool does

- **Tools in `tool.py`**: A **`Tool`** class wraps each function (`name`, `description`, `fn`); call **`tool.execute(**kwargs)`** to run it. Three tools:
  - **`count_sentence`**: Counts sentences (`.`, `!`, `?` followed by whitespace or end).
  - **`count_words`**: Counts words (alphanumeric/apostrophe tokens).
  - **`parse_date`**: Parses a datetime string with timezone and converts to **HKT** ISO 8601 (e.g. `2026-02-27T21:30:00+08:00`).
- **Demo workflow (1 agent + tools)**
  - **`demo.py`** uses a single agent (**`NewsGeneratorAgent`**) that calls the DeepSeek chat API (max 1K tokens) to generate **one single-paragraph news article (~500–600 words)**.
  - The **first word** of the paragraph is a datetime with timezone; `demo.py` extracts it and runs the tools via **`Tool.execute(...)`** for parse_date, count_sentence, and count_words.
  - The final output is a dict like:
    - `{"results": [{"datetime_hkt": "YYYY-MM-DDThh:mm:ss+08:00", "sentences": int, "words": int, "article": "string"}]}`.

### How to run the demo

- **1. Install dependencies**
  - Python 3.10+ is recommended.
  - Install packages (in your virtualenv or environment):
    - `pip install openai python-dotenv`
- **2. Configure DeepSeek**
  - Create a `.env` file in the project root (same folder as `tool.py`) with your own credentials:
    - **`DEEPSEEK_API_KEY`**: your personal DeepSeek API key, e.g. `DEEPSEEK_API_KEY=sk-...`
    - **`DEEPSEEK_API_BASE`**: usually `https://api.deepseek.com`
    - **`DEEPSEEK_MODEL`**: e.g. `deepseek-chat`
  - Keep `.env` **out of version control** (e.g. via `.gitignore`) so your key is not committed.
- **3. Run the demo script**
  - From the project root:
    - `python demo.py`
  - The script runs the single agent (DeepSeek), then uses the tools from `tool.py`, and pretty‑prints the JSON result to the console.
  - If DeepSeek fails or returns unexpected JSON, or the output schema is wrong, `demo.py` prints an error to stderr and exits with a non‑zero code.

### Design decisions and limitations

- **Design decisions**
  - **One agent**: The pipeline uses a single agent (`NewsGeneratorAgent` in `demo.py`) for LLM calls; tools in `tool.py` are applied after generation.
  - **Tool class**: Each tool is a `Tool(name, description, fn)` invoked via `execute(**kwargs)`; `tool.py` also exposes the underlying pure functions.
  - **Separation of concerns**: DeepSeek prompting/parsing is kept in the demo script (inside the agent), while `tool.py` focuses purely on text and datetime utilities.
  - **Robust but simple parsing**: DeepSeek responses are expected to be JSON; `demo.py` has a small fallback that extracts the first JSON object if extra text is present.
  - **Clear error propagation**: Low‑level errors raise exceptions; `demo.py` catches them, reports a readable error, and exits non‑zero so callers can detect failure.
- **Limitations**
  - **Model response assumptions**: The code assumes DeepSeek returns well‑formed JSON with an `articles` list and an `article` string; if the structure changes, parsing may fail.
  - **Datetime parsing**: `parse_date()` relies on ISO 8601 offsets or a small set of explicit patterns; unusual datetime formats may raise errors.
  - **Sentence and word counting**: Both rely on simple regexes; edge cases like abbreviations (`U.S.`), decimals (`3.14`), or emojis may affect counts.
  - **No tests or logging**: To keep things minimal and follow the project rules, there are no automated tests and no logging framework—only basic exceptions and console output in `demo.py`.
