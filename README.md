# Wordle Solver

A command-line Python script that narrows down possible Wordle answers based on your known letter clues.

## Requirements

- Python 3.x
- A `dictionary.txt` file in the same directory as the script (one word per line)

## Usage

Run the script from your terminal:

```bash
python wordle_solver.py
```

The script will prompt you for three pieces of information based on your current Wordle game state:

### 1. Confirmed Letters
Letters you know are in the word (shown in **yellow** or **green** by Wordle).

```
Enter confirmed letters separated by a comma: a,e,r
```

### 2. Eliminated Letters
Letters you know are **not** in the word (shown in **grey** by Wordle).

```
Enter letters confirmed to be not used separated by a comma: t,s,n
```

### 3. Incorrect Positions
For each confirmed letter, enter the positions (0–4) where you know it does **not** belong (yellow tiles). If a letter has no position restrictions, just press Enter.

```
Enter positions (0-4) confirmed not to be used for a : 0,2
Enter positions (0-4) confirmed not to be used for e : 4
Enter positions (0-4) confirmed not to be used for r : 1
```

> **Position index reference:**
> | Index | 0 | 1 | 2 | 3 | 4 |
> |-------|---|---|---|---|---|
> | Letter | W | O | R | D | S |

### Output

The script prints a list of all matching words and a result count:

```
['baler', 'carer', 'parer', 'raker', 'raver', 'razer']
Returned 6 results.
```

## Example Walkthrough

Suppose your Wordle board looks like this after two guesses:

- You know the word contains **A**, **R**, and **E**
- **T**, **S**, and **N** are eliminated
- **A** is not in position 0 or 2
- **R** is not in position 2
- **E** is not in position 1

```
Enter confirmed letters separated by a comma: a,r,e
Enter letters confirmed to be not used separated by a comma: t,s,n
Enter positions (0-4) confirmed not to be used for a : 0,2
Enter positions (0-4) confirmed not to be used for r : 2
Enter positions (0-4) confirmed not to be used for e : 1
```

## Notes

- The script reads words from `dictionary.txt` — make sure this file is present and contains 5-letter words for best results. A standard Wordle word list works well.
- Position indices are **0-based** (0 = first letter, 4 = last letter).
- If a confirmed letter has no incorrect-position constraints, leave the prompt blank and press Enter.
