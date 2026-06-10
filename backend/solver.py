import json
import math
import os
import random

_DICT_PATH = os.path.join(os.path.dirname(__file__), "dictionary.txt")
_OPENERS_PATH = os.path.join(os.path.dirname(__file__), "openers.json")
_ALL_WORDS = None
_OPENERS = None

# Cap on guess×answer pattern simulations per request, sized to stay well
# under the Lambda timeout. Scoring the full dictionary against thousands of
# candidates would take minutes otherwise.
_MAX_SIMS = 4_000_000


def load_words():
    global _ALL_WORDS
    if _ALL_WORDS is None:
        with open(_DICT_PATH) as f:
            _ALL_WORDS = [w.strip().upper() for w in f if len(w.strip()) == 5]
    return _ALL_WORDS


def simulate_result(guess, answer):
    result = ["X"] * 5
    answer_chars = list(answer)
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
            answer_chars[i] = None
    for i in range(5):
        if result[i] == "G":
            continue
        if guess[i] in answer_chars:
            result[i] = "Y"
            answer_chars[answer_chars.index(guess[i])] = None
    return "".join(result)


def filter_words(word_list, guess, result):
    return [w for w in word_list if simulate_result(guess, w) == result]


def rank_by_frequency(candidates):
    letter_freq = {}
    for word in candidates:
        for letter in set(word):
            letter_freq[letter] = letter_freq.get(letter, 0) + 1
    scored = {w: sum(letter_freq.get(l, 0) for l in set(w)) for w in candidates}
    return sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))


def rank_by_information_gain(all_words, candidates):
    n = len(candidates)
    if n == 0:
        return []
    candidate_set = set(candidates)

    # Stay within the simulation budget: first narrow the guess pool to the
    # candidates themselves, then sample the answer set if still over. The
    # entropy estimate from a large sample is accurate enough for ranking.
    guess_pool = all_words
    if len(guess_pool) * n > _MAX_SIMS:
        guess_pool = candidates
    answers = candidates
    if len(guess_pool) * n > _MAX_SIMS:
        answers = random.sample(candidates, _MAX_SIMS // len(guess_pool))
        n = len(answers)

    max_entropy = math.log2(n) if n > 1 else 1
    scored = []
    for guess in guess_pool:
        buckets = {}
        for answer in answers:
            pattern = simulate_result(guess, answer)
            buckets[pattern] = buckets.get(pattern, 0) + 1
        entropy = sum(-c / n * math.log2(c / n) for c in buckets.values())
        scored.append({
            "word": guess,
            "score": round((entropy / max_entropy) * 100, 1),
            "is_candidate": guess in candidate_set,
        })
    return sorted(scored, key=lambda x: (-x["score"], x["word"]))


def load_openers():
    global _OPENERS
    if _OPENERS is None:
        with open(_OPENERS_PATH) as f:
            _OPENERS = json.load(f)
    return _OPENERS


def solve(guesses):
    """
    guesses: list of {"word": "CRANE", "result": "GXYXG"}
    returns: {"candidates_count": n, "frequency_ranked": [...], "info_ranked": [...]}
    """
    if not guesses:
        return load_openers()

    all_words = load_words()
    candidates = all_words[:]

    for g in guesses:
        candidates = filter_words(candidates, g["word"].upper(), g["result"].upper())

    if not candidates:
        return {"candidates_count": 0, "frequency_ranked": [], "info_ranked": []}

    return {
        "candidates_count": len(candidates),
        "frequency_ranked": [{"word": w, "score": s} for w, s in rank_by_frequency(candidates)[:20]],
        "info_ranked": rank_by_information_gain(all_words, candidates)[:20],
    }
