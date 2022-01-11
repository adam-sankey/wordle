#get letters used and not used and assign to variables
letters = input("Enter confirmed letters separated by a comma: ")
notLetters = input("Enter letters confirmed to be not used separated by a comma: ")

#convert strings to lists
letters = letters.split(",")
notLetters = notLetters.split(",")

#assign list lenght to a variable
numLetters = len(letters)
numNotLetters = len(notLetters)

#create dictionary
letterPositions = {}

#get confirmed non-position of letters
for letter in letters:
    letterPositions[letter] = input("Enter positions (0-4) confirmed not to be used for " + letter + " : ")
    letterPlaceHolder = letterPositions[letter]
    letterPositions[letter] = letterPlaceHolder.split(",")

#open dictionary file
dictionary = open("dictionary.txt", "r")

#create list variable
wordList = []

#begin looping through each word in dictionary file
for word in dictionary:
 
    #create score variable used for determining if all confirmed letters are used in a word
    score = 0

    #verify if all confirmed letters are in the given word
    #if all letters are present in the word, add the word to wordList
    for letter in letters:
        if letter in word:
            score += 1
        if score == numLetters:
            wordList.append(word)
    
    #verify if any of the letters confirmed not to be present are in the given word
    #remove the word from wordList is any of the notLetters exist
    for letter in notLetters:
        if letter in word:
            try:
                wordList.remove(word)
            except ValueError:
                pass

    #verify confirmed words are not using the confirmed letters in an incorrect place
    #remove words with letters in the wrong place from the wordList
    for letter in letters:
        for position in letterPositions[letter]:
            position = int(position)
            try:
                if letter in word[position]:
                    wordList.remove(word)
            except ValueError:
                pass            

#create cleaned up word list dictionary
prettyWordList = []

#create cleaned up word list
for y in wordList:
    y = y.strip()
    prettyWordList.append(y)

#display possible words
print(prettyWordList)
print("Returned ", len(prettyWordList), " results." )

#close dictionary file
dictionary.close()
