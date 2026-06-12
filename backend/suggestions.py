"""Prompt pieces shared by the Claude and Gemini suggestion handlers."""

TOP_N = 10

SYSTEM_PROMPT = (
    "You are an expert Wordle strategist. Given a solver's ranked word lists and "
    "the game history, recommend the single best next guess and briefly explain why."
)


def build_prompt(guesses, data):
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
