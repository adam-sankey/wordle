import json
import os
import re
import urllib.error
import urllib.request

import boto3

from solver import solve
from suggestions import SYSTEM_PROMPT, build_prompt

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# Alias that tracks Google's newest stable Flash model — the free tier covers
# Flash models, and pinned versions get shut down (2.0 Flash died June 2026)
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

# Gemini's responseSchema uses OpenAPI-style uppercase types and rejects
# additionalProperties, so this can't share the Claude schema
OUTPUT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "recommendation": {
            "type": "STRING",
            "description": "The single 5-letter word to guess next, in uppercase",
        },
        "reasoning": {
            "type": "STRING",
            "description": "2-3 sentences explaining the choice",
        },
    },
    "required": ["recommendation", "reasoning"],
}

_api_key = None


def _get_api_key():
    global _api_key
    if _api_key is None:
        # The key lives in a different region than the stack
        ssm = boto3.client("ssm", region_name=os.environ.get("GEMINI_PARAM_REGION", "us-west-1"))
        _api_key = ssm.get_parameter(
            Name=os.environ.get("GEMINI_API_KEY_PARAM", "gemini"),
            WithDecryption=True,
        )["Parameter"]["Value"]
    return _api_key


def _ask_gemini(prompt):
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": OUTPUT_SCHEMA,
            # Thinking tokens count toward this limit on Flash models, so
            # leave generous headroom above the small JSON answer
            "maxOutputTokens": 4096,
        },
    }
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": _get_api_key()},
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read())
    parts = data["candidates"][0]["content"]["parts"]
    text = next(p["text"] for p in parts if "text" in p and not p.get("thought"))
    return json.loads(text)


def lambda_handler(event, context):
    if event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {"statusCode": 204, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
        guesses = body.get("guesses", [])

        if not isinstance(guesses, list) or len(guesses) > 6:
            return _error(400, "guesses must be a list of up to 6 items")

        for g in guesses:
            if not re.match(r"^[A-Za-z]{5}$", g.get("word", "")):
                return _error(400, f"invalid word: {g.get('word', '')!r}")
            if not re.match(r"^[GYXgyx]{5}$", g.get("result", "")):
                return _error(400, f"invalid result: {g.get('result', '')!r}")

        data = solve(guesses)

        if data["candidates_count"] == 0:
            return _error(400, "no matching words - check your inputs")

        if data["candidates_count"] == 1:
            word = data["frequency_ranked"][0]["word"]
            return _ok({
                "recommendation": word,
                "reasoning": "Only one possible word remains, so it must be the answer.",
            })

        result = _ask_gemini(build_prompt(guesses, data))

        return _ok({
            "recommendation": result["recommendation"].upper(),
            "reasoning": result["reasoning"],
        })

    except urllib.error.URLError:
        return _error(502, "the AI service is unavailable - please try again")
    except Exception:
        return _error(500, "internal error")


def _ok(payload):
    return {"statusCode": 200, "headers": HEADERS, "body": json.dumps(payload)}


def _error(status, message):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps({"error": message})}
