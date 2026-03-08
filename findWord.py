letters = input("Enter confirmed letters separated by a comma: ")
letters = letters.split(",")

notLetters = input("Enter letters confirmed to be not used separated by a comma: ")
notLetters = notLetters.split(",")

dictionary = open("5lw.txt", "r")

wordList = []

for word in dictionary:
    if 'R' in word and 'U' in word and 'E' in word:
        wordList.append(word)

for word in wordList:
    if 'A' in word or 'T' in word or 'S' in word or 'G' in word or 'O' in word or 'P' in word or 'F' in word or 'M' in word:
        wordList.remove(word)

prettyWordList = []

for y in wordList:
    y = y.strip()
    prettyWordList.append(y)    

print(prettyWordList)

dictionary.close()



letters = input("Enter confirmed letters separated by a comma: ")
letters = letters.split(",")

notLetters = input("Enter letters confirmed to be not used separated by a comma: ")
notLetters = notLetters.split(",")

dictionary = open("5lw.txt", "r")

wordList = []

numLetters = len(letters)
numNotLetters = len(notLetters)

for word in dictionary:
    x = 0
    score = 0
    notScore = 0
    while x < numLetters:
        if letters[x] in word:
            score += 1
        x += 1
        if score == numLetters:
            wordList.append(word)
    while x < numNotLetters:
        if notLetters[x] in word:
            notScore += 1
        x += 1
        if notScore >= 1:
            wordList.remove(word)

    

prettyWordList = []

for y in wordList:
    y = y.strip()
    prettyWordList.append(y)    

print(prettyWordList)

dictionary.close()
