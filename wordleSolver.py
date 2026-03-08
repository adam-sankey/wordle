"""
Wordle Solver
-------------
Usage per round:
  1. Enter the 5-letter word you guessed.
  2. For each letter, enter its result:
       G = Green  (correct letter, correct position)
       Y = Yellow (correct letter, wrong position)
       X = Grey   (letter not in word)

After each round, two ranked lists are shown:
  - Frequency Score : ranks candidate words by how common their letters
                      are across all remaining candidates.
  - Information Gain: ranks ALL dictionary words by how evenly they split
                      the remaining candidates across possible outcomes.
                      Words marked with * are also valid candidates.
"""

import math


# ---------------------------------------------------------------------------
# FILE LOADING
# ---------------------------------------------------------------------------

def load_words(path="dictionary.txt"):
    """Read the dictionary file and return a list of valid 5-letter words.
    Words are stripped of whitespace and converted to uppercase so all
    comparisons throughout the script are case-insensitive."""
    with open(path, "r") as f:
        return [w.strip().upper() for w in f if len(w.strip()) == 5]


# ---------------------------------------------------------------------------
# USER INPUT
# ---------------------------------------------------------------------------

def get_guess():
    """Prompt the user to enter their guessed word and validate it.
    Loops until a valid 5-letter alphabetic word is entered."""
    while True:
        word = input("\nEnter your guessed word: ").strip().upper()
        if len(word) == 5 and word.isalpha():
            return word
        print("  Please enter exactly 5 letters.")


def get_result(word):
    """Prompt the user to enter the colour result Wordle returned for their guess.
    Each character represents one position: G=Green, Y=Yellow, X=Grey.
    Loops until a valid 5-character string using only G, Y, and X is entered."""
    print(f"  Enter result for '{word}' — one character per letter.")
    print("  G = Green (right place)  Y = Yellow (wrong place)  X = Grey (not in word)")
    while True:
        result = input("  Result (e.g. GXYXG): ").strip().upper()
        if len(result) == 5 and all(c in "GYX" for c in result):
            return result
        print("  Invalid input. Use exactly 5 characters: G, Y, or X only.")


# ---------------------------------------------------------------------------
# WORDLE RESULT SIMULATION
# ---------------------------------------------------------------------------

def simulate_result(guess, answer):
    """Simulate what colour result Wordle would return if 'guess' were played
    and 'answer' is the correct word.

    Wordle's colouring rules use two passes to handle duplicate letters correctly:

    Pass 1 — Greens: scan every position. If the guessed letter matches the
    answer letter at the same position, mark it Green and remove that answer
    letter from the pool so it cannot be matched again.

    Pass 2 — Yellows: for each non-Green position, check whether the guessed
    letter still exists in the remaining answer pool. If it does, mark it Yellow
    and remove it from the pool. If not, leave it as Grey (X).

    This two-pass approach ensures that a letter in the guess is never awarded
    more matches (Green or Yellow) than the number of times it actually appears
    in the answer."""

    # Start every position as Grey; we'll upgrade to G or Y as matches are found
    result = ["X"] * 5

    # Work on a mutable copy of the answer so we can 'claim' letters as they match
    answer_chars = list(answer)

    # --- Pass 1: Greens ---
    for i in range(5):
        if guess[i] == answer[i]:
            result[i] = "G"
            # Mark this answer letter as used so it isn't matched again in pass 2
            answer_chars[i] = None

    # --- Pass 2: Yellows ---
    for i in range(5):
        # Skip positions already confirmed Green
        if result[i] == "G":
            continue
        # If the guessed letter exists anywhere in the remaining answer pool,
        # it's a Yellow — right letter, wrong position
        if guess[i] in answer_chars:
            result[i] = "Y"
            # Claim this answer letter so duplicate guessed letters don't
            # each get credited with the same answer letter
            answer_chars[answer_chars.index(guess[i])] = None

    return "".join(result)


# ---------------------------------------------------------------------------
# FILTERING
# ---------------------------------------------------------------------------

def filter_words(word_list, guess, result):
    """Reduce word_list to only the words that are still possible answers.

    For each candidate word, we simulate what result Wordle would have returned
    if that candidate were the answer and the user's guess were played against it.
    If the simulated result matches the actual result the user entered, the word
    remains a valid candidate. If it doesn't match, the word is eliminated.

    Using simulate_result here (rather than manually checking Green/Yellow/Grey
    rules) means duplicate-letter handling is automatically correct."""
    return [word for word in word_list if simulate_result(guess, word) == result]


# ---------------------------------------------------------------------------
# SCORING — METHOD 1: LETTER FREQUENCY
# ---------------------------------------------------------------------------

def rank_by_frequency(candidates):
    """Score each remaining candidate by how common its unique letters are
    across all other candidates.

    Step 1 — Build a frequency table: for each letter of the alphabet, count
    how many candidate words contain that letter (each word counted once per
    letter regardless of how many times the letter appears in that word).

    Step 2 — Score each word: sum the frequency table values for each of the
    word's unique letters. A word made up of letters that appear in many other
    candidates scores highly because, whatever Wordle returns for that guess,
    the result carries information about letters that are widely relevant.

    Words are returned sorted highest score first, then alphabetically to break
    ties consistently."""

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Step 1: count how many candidate words contain each letter
    letter_freq = {l: 0 for l in alphabet}
    for word in candidates:
        for letter in set(word):        # set() so each letter counted once per word
            letter_freq[letter] += 1

    # Step 2: score each word by summing frequencies of its unique letters
    word_scores = {}
    for word in candidates:
        word_scores[word] = sum(letter_freq[l] for l in set(word))

    return sorted(word_scores.items(), key=lambda kv: (-kv[1], kv[0]))


# ---------------------------------------------------------------------------
# SCORING — METHOD 2: INFORMATION GAIN (ENTROPY)
# ---------------------------------------------------------------------------

def rank_by_information_gain(all_words, candidates):
    """Score every word in the full dictionary by how much information it
    would reveal about the answer if guessed next.

    The core idea: a great guess is one where the result Wordle returns narrows
    down the candidates as much as possible, regardless of which result comes back.
    A poor guess is one where one result is overwhelmingly likely (e.g. all
    remaining candidates produce the same pattern), so you learn almost nothing.

    HOW IT WORKS:

    For each potential guess word, we simulate the result pattern it would
    produce against every remaining candidate. We then group candidates into
    'buckets' by their pattern — each bucket contains all the candidates that
    would survive if that pattern came back. A guess that creates many similarly-
    sized buckets is more informative than one that dumps almost all candidates
    into a single bucket.

    We measure this using Shannon entropy:
        entropy = sum of  -p * log2(p)  for each bucket
    where p is the fraction of candidates in that bucket. Entropy is maximised
    when all buckets are equally sized (perfectly informative guess) and is zero
    when there is only one bucket (completely uninformative guess).

    SCALING:
    Raw entropy is in 'bits' and varies with the number of candidates, making
    it hard to compare across rounds. We scale it to 0-100 by dividing by the
    theoretical maximum entropy for this round (log2 of the number of candidates),
    which represents the hypothetical perfect guess that puts each candidate in
    its own unique bucket.

    NOTE: Unlike the frequency method, this searches the entire dictionary —
    not just remaining candidates — because sometimes a non-candidate word
    produces a better split of the candidate pool than any candidate word would.
    Non-candidate words are marked with a space; candidate words are marked *."""

    n = len(candidates)
    if n == 0:
        return []

    # Pre-build a set for fast candidate membership checks
    candidate_set = set(candidates)

    # Theoretical maximum entropy: every candidate lands in its own bucket
    max_entropy = math.log2(n) if n > 1 else 1

    scored = []

    for guess in all_words:

        # --- Build pattern buckets ---
        # Key: result pattern string (e.g. "GXYXG")
        # Value: number of candidates that would produce this pattern
        buckets = {}
        for answer in candidates:
            pattern = simulate_result(guess, answer)
            buckets[pattern] = buckets.get(pattern, 0) + 1

        # --- Calculate Shannon entropy across buckets ---
        entropy = 0.0
        for count in buckets.values():
            p = count / n                   # fraction of candidates in this bucket
            entropy -= p * math.log2(p)     # entropy contribution of this bucket

        # --- Scale entropy to 0-100 ---
        scaled_score = round((entropy / max_entropy) * 100, 1)

        # Track whether this guess word is itself a valid remaining candidate
        is_candidate = guess in candidate_set

        scored.append((guess, scaled_score, is_candidate))

    # Sort highest score first, alphabetically to break ties
    return sorted(scored, key=lambda x: (-x[1], x[0]))


# ---------------------------------------------------------------------------
# DISPLAY
# ---------------------------------------------------------------------------

def display_results(freq_ranked, info_ranked, total_candidates):
    """Print both ranked word lists to the console after each round."""

    print(f"\n  {total_candidates} possible word(s) remaining.")

    # --- Frequency list ---
    print("\n  --- Frequency Score (candidates only) ---")
    print("  Ranks remaining candidates by how common their letters are")
    print("  across all other candidates. Higher = more letters in common.")
    print()
    for word, score in freq_ranked[:20]:
        print(f"    {word}   score: {score}")
    if len(freq_ranked) > 20:
        print(f"    ... and {len(freq_ranked) - 20} more candidates.")

    # --- Information gain list ---
    print("\n  --- Information Gain Score (all words) ---")
    print("  Ranks all dictionary words by how evenly they split the")
    print("  remaining candidates. Higher = narrows the pool more reliably.")
    print("  Words marked * are also valid candidates.")
    print()
    for word, score, is_candidate in info_ranked[:20]:
        # Mark valid candidates with * so the user knows they could be the answer
        marker = "*" if is_candidate else " "
        print(f"  {marker} {word}   score: {score}/100")
    if len(info_ranked) > 20:
        print(f"    ... and {len(info_ranked) - 20} more.")


# ---------------------------------------------------------------------------
# MAIN GAME LOOP
# ---------------------------------------------------------------------------

def main():
    """Run the solver for a full Wordle game.

    Loads the dictionary once, then loops round-by-round:
      1. Prompt the user for their guess and Wordle's result.
      2. Filter the candidate list down to words still consistent with all
         results seen so far.
      3. Score and display the remaining candidates using both methods.
      4. Repeat until the game is won, one candidate remains, or no candidates
         remain (which would indicate a data entry error or a missing word)."""

    print("=" * 50)
    print("           W O R D L E   S O L V E R")
    print("=" * 50)

    # Load all 5-letter words from the dictionary file
    all_words = load_words()
    if not all_words:
        print("Error: dictionary.txt not found or empty.")
        return

    # At the start of the game every word is a candidate
    candidates = all_words[:]
    round_num = 1

    while True:
        print(f"\n--- Round {round_num} ---")

        # If the candidate pool is empty something went wrong with input
        if not candidates:
            print("  No words remaining — the dictionary may not contain the answer.")
            break

        # If only one candidate remains it must be the answer
        if len(candidates) == 1:
            print(f"  The answer must be: {candidates[0]}")
            break

        # Get the user's guess and the result Wordle returned
        guess = get_guess()
        result = get_result(guess)

        # All-green means the user just guessed correctly
        if result == "GGGGG":
            print(f"\n  Solved in {round_num} round(s)! The word was {guess}. 🎉")
            break

        # Narrow the candidate list based on this round's guess and result
        candidates = filter_words(candidates, guess, result)

        if not candidates:
            print("\n  No matching words found. Check your inputs and try again.")
            break

        # Calculate both rankings and display them
        # The progress dots give feedback during the slower information gain calculation
        print("\n  Calculating scores", end="", flush=True)
        freq_ranked = rank_by_frequency(candidates)
        print(".", end="", flush=True)
        info_ranked = rank_by_information_gain(all_words, candidates)
        print(". done.")

        display_results(freq_ranked, info_ranked, len(candidates))

        round_num += 1


# Entry point — only run main() if this file is executed directly,
# not if it is imported as a module by another script
if __name__ == "__main__":
    main()
