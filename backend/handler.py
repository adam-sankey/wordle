import json
import re

from solver import solve

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


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

        return {"statusCode": 200, "headers": HEADERS, "body": json.dumps(solve(guesses))}

    except Exception:
        return _error(500, "internal error")


def _error(status, message):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps({"error": message})}
