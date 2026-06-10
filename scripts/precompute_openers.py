"""Generate backend/openers.json — the precomputed first-guess suggestions.

Ranking openers means scoring every dictionary word against every possible
answer (~155M pattern simulations), which takes minutes. That's far too slow
for a Lambda request, so we compute it once here and ship the result.

Re-run whenever backend/dictionary.txt changes:
    python3 scripts/precompute_openers.py
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from solver import load_words, rank_by_frequency, rank_by_information_gain

OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "openers.json")


def main():
    words = load_words()
    print(f"Ranking openers across {len(words)} words — this takes a few minutes...")

    start = time.time()
    info_ranked = rank_by_information_gain(words, words)[:20]
    print(f"Information gain done in {time.time() - start:.0f}s")

    freq_ranked = [{"word": w, "score": s} for w, s in rank_by_frequency(words)[:20]]

    with open(OUT_PATH, "w") as f:
        json.dump(
            {
                "candidates_count": len(words),
                "frequency_ranked": freq_ranked,
                "info_ranked": info_ranked,
            },
            f,
            indent=2,
        )
    print(f"Wrote {OUT_PATH}")
    print("Top openers:", ", ".join(e["word"] for e in info_ranked[:5]))


if __name__ == "__main__":
    main()
