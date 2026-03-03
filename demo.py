"""
Demo script that calls DeepSeek, then applies local tools in `tool.py`.

This script:
- Calls DeepSeek to generate 1 news article (single paragraph, ~500-600 words).
- The article starts with a datetime (the FIRST word) with a timezone/offset.
- Uses `parse_date()` to convert to HKT ISO 8601.
- Uses `count_sentence()` and `count_words()` to compute basic text stats.
- Prints one JSON-serialisable dict to stdout.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional

from tool import count_sentence, count_words, parse_date


def _safe_load_dotenv() -> None:
    """Load `.env` variables if possible (with a simple fallback)."""

    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv()
        return
    except Exception:
        pass

    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        return


def _extract_json_object(text: str) -> Optional[str]:
    if not text:
        return None
    m = re.search(r"\{[\s\S]*\}", text)
    return m.group(0) if m else None


def _deepseek_generate_articles() -> List[Dict[str, str]]:
    """
    Call DeepSeek and return a list with 1 item:
      [{"article": "..."}]
    """

    _safe_load_dotenv()
    api_key = (os.getenv("DEEPSEEK_API_KEY") or "").strip()
    api_base = (os.getenv("DEEPSEEK_API_BASE") or "https://api.deepseek.com").strip()
    model = (os.getenv("DEEPSEEK_MODEL") or "deepseek-chat").strip()

    if not api_key:
        raise RuntimeError("Missing DEEPSEEK_API_KEY in environment/.env")

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        raise RuntimeError(f"Missing dependency for DeepSeek client (openai). {e}") from e

    client = OpenAI(api_key=api_key, base_url=api_base)

    # Requested base prompt + explicit datetime/timezone requirement for this demo.
    prompt = (
        "Generate 1 piece of 500-600 words news article as ONE single paragraph.\n"
        "The FIRST word of the paragraph must be the datetime with timezone, with NO surrounding brackets.\n"
        "Example first word: 2026-02-27T14:30:00+02:00\n"
        "Use numeric timezone offsets (e.g. +09:00, -04:00, Z) to avoid ambiguity."
    )
    schema_hint = (
        "Return ONLY valid JSON in this format:\n"
        '{\n  "articles": [\n'
        '    {"article": "string"}\n'
        "  ]\n}\n"
        "Rules:\n"
        "- Exactly 1 item.\n"
        "- The paragraph's FIRST word must be the datetime and MUST include timezone info.\n"
        "- The article must be a SINGLE paragraph and ~500-600 words.\n"
    )

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.4,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": "You must respond with valid JSON only."},
                {"role": "user", "content": f"{prompt}\n\n{schema_hint}"},
            ],
        )
        content = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        raise RuntimeError(f"DeepSeek API request failed (check API key/base/model). {e}") from e

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        extracted = _extract_json_object(content)
        if not extracted:
            raise ValueError("DeepSeek returned non-JSON output")
        data = json.loads(extracted)

    articles = data.get("articles") if isinstance(data, dict) else None
    if not isinstance(articles, list) or len(articles) == 0:
        raise ValueError("DeepSeek returned invalid schema (missing articles list)")

    cleaned: List[Dict[str, str]] = []
    for item in articles[:1]:
        if not isinstance(item, dict):
            continue
        art = (item.get("article") or "").strip()
        if art:
            cleaned.append({"article": art})

    if len(cleaned) == 0:
        raise ValueError("DeepSeek returned empty/invalid articles")
    return cleaned[:1]


def _validate_output_schema(result: Any) -> Dict[str, Any]:
    """
    Validate output is JSON-serialisable and matches expected schema:
      {"results": [{"datetime_hkt": str, "sentences": int, "words": int, "article": str}, ...]}
    """

    if not isinstance(result, dict):
        raise ValueError("Result must be a dict")
    results = result.get("results")
    if not isinstance(results, list) or len(results) == 0:
        raise ValueError('Missing/invalid "results" list')
    for i, item in enumerate(results):
        if not isinstance(item, dict):
            raise ValueError(f"results[{i}] must be a dict")
        for key in ("datetime_hkt", "sentences", "words", "article"):
            if key not in item:
                raise ValueError(f'Missing key "{key}" in results[{i}]')
    encoded = json.dumps(result, ensure_ascii=False)
    json.loads(encoded)
    return result


def main() -> None:
    try:
        generated = _deepseek_generate_articles()
    except Exception as e:
        print(f"DEMO ERROR: DeepSeek error/bad input: {e}", file=sys.stderr)
        raise SystemExit(1)

    results: List[Dict[str, Any]] = []
    for item in generated:
        article = item["article"]
        first_word = article.strip().split(None, 1)[0] if article.strip() else ""
        if not first_word:
            raise ValueError("Generated article is empty")

        # The first word is expected to be the datetime with timezone/offset.
        dt_hkt = parse_date(first_word)
        sentences = count_sentence(article)
        words = count_words(article)
        results.append(
            {
                "datetime_hkt": dt_hkt,
                "sentences": int(sentences),
                "words": int(words),
                "article": article,
            }
        )

    output: Dict[str, Any] = {"results": results}
    try:
        validated = _validate_output_schema(output)
    except Exception as e:
        print(f"DEMO ERROR: Invalid output JSON: {e}", file=sys.stderr)
        raise SystemExit(1)

    print(json.dumps(validated, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()