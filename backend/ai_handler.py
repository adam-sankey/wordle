import json
import os
import re

import anthropic
import boto3

from solver import solve

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

MODEL = "claude-haiku-4-5"
TOP_N = 10

SYSTEM_PROMPT = (
    "You are an expert Wordle strategist. Given a solver's ranked word lists and "
    "the game history, recommend the single best next guess and briefly explain why."
)

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendation": {
            "type": "string",
            "description": "The single 5-letter word to guess next, in uppercase",
        },
        "reasoning": {
            "type": "string",
            "description": "2-3 sentences explaining the choice",
        },
    },
    "required": ["recommendation", "reasoning"],
    "additionalProperties": False,
}

_client = None


def _get_client():
    global _client
    if _client is None:
        ssm = boto3.client("ssm")
        api_key = ssm.get_parameter(
            Name=os.environ.get("CLAUDE_API_KEY_PARAM", "claude"),
            WithDecryption=True,
        )["Parameter"]["Value"]
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _build_prompt(guesses, data):
    lines = [
        "We are playing a Wordle-style game: find a hidden 5-letter word. After each "
        "guess, every letter gets a result: G = green (correct letter, correct position), "
        "Y = yellow (letter is in the word but in a different position), X = grey "
        "(letter is not in the word).",
        "",
    ]

    if guesses:
        lines.append("Game history this session (guess -> per-letter result):")
        for i, g in enumerate(guesses, 1):
            lines.append(f"{i}. {g['word'].upper()} -> {g['result'].upper()}")
    else:
        lines.append("No guesses have been made yet - we are choosing an opening word.")

    lines += [
        "",
        f"{data['candidates_count']} possible answers remain.",
        "",
        "Our solver produced two ranked lists of suggestions.",
        "",
        "FREQUENCY SCORE (top 10) - candidates ranked by how common their letters are "
        "across the remaining possible answers. Every word in this list is a valid "
        "possible answer:",
    ]
    for i, item in enumerate(data["frequency_ranked"][:TOP_N], 1):
        lines.append(f"{i}. {item['word']} (score {item['score']})")

    lines += [
        "",
        "INFORMATION GAIN (top 10) - words ranked by how evenly they split the "
        "remaining candidates, i.e. how many possibilities they are expected to "
        "eliminate. Words marked with * are valid possible answers; unmarked words "
        "cannot be the answer but may eliminate more words. Information gain is most "
        "useful on the second and third guesses:",
    ]
    for i, item in enumerate(data["info_ranked"][:TOP_N], 1):
        star = "*" if item.get("is_candidate") else ""
        lines.append(f"{i}. {item['word']}{star} ({item['score']}/100)")

    lines += [
        "",
        "Recommend the single best next guess. Weigh the tradeoff: with many candidates "
        "remaining, a high-information-gain word (even one that cannot be the answer) "
        "is usually best; with only a few candidates left, guess the most likely valid "
        "answer. Pick a word from one of the lists above.",
    ]
    return "\n".join(lines)


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

        response = _get_client().messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(guesses, data)}],
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
        text = next(b.text for b in response.content if b.type == "text")
        result = json.loads(text)

        return _ok({
            "recommendation": result["recommendation"].upper(),
            "reasoning": result["reasoning"],
        })

    except anthropic.APIError:
        return _error(502, "the AI service is unavailable - please try again")
    except Exception:
        return _error(500, "internal error")


def _ok(payload):
    return {"statusCode": 200, "headers": HEADERS, "body": json.dumps(payload)}


def _error(status, message):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps({"error": message})}
