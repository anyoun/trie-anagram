#TODO: Take search at command-line optionally for piping output
#TODO: Print words that matched together on the same line
#      When we hit a word, both keep going and restart from root with fewer chars

import sys, os, readline, argparse

global nodeCount, wordCount
nodeCount = 0
wordCount = 0

class Word:
    def __init__(self, word, frequency, subcategory):
        self.word = word
        self.frequency = frequency
        self.subcategory = subcategory
    def __str__(self):
        return '%s (%i%% %s)' % (self.word, self.frequency, self.subcategory)
    def weight(self):
        return len(self.word) * 10 + self.frequency

class TrieNode(object):
    def __init__(self):
        super(TrieNode, self).__init__()
        global nodeCount
        self.children = { }
        self.words = [ ]
        nodeCount += 1
    def getChild(self, char):
        if char not in self.children:
            n = TrieNode()
            self.children[char] = n
            return n
        else:
            return self.children[char]
    def getChildren(self):
        return self.children.values()
    def addWord(self, word, frequency, subcategory):
        self.words.append(Word(word, frequency, subcategory))
    def getWords(self):
        return self.words
    def toString(self, indent = 0):
        s = "{ "
        for char,node in self.children.items():
            s += "\n%s%s: %s" % (' '*indent, char, node.toString(indent+1))
        s += " }"
        for word in self.words:
            s += " " + word
        return s

def calcWordSetWeight(wordSet):
    return sum(map(lambda w: w.weight(), wordSet))

def wordToChars(word):
    word = word.strip().strip('.').lower()
    # chars = [x for x in word]
    chars = list(word)
    chars.sort() #What about sorting by character frequency?
    return chars

def addFileToTrie(rootNode, filePath, frequency, subcategory):
    if not os.path.exists(filePath):
        return
    f = open(filePath, 'r')
    for line in f:
        node = rootNode
        if '\'' in line:
            continue
        word = line.strip()
        for char in wordToChars(word):
            node = node.getChild(char)
        node.addWord(word, frequency, subcategory)
        global wordCount
        wordCount += 1
    return rootNode

def buildTrie():
    rootNode = TrieNode()
    sizes = [ 10, 20, 35, 40, 50, 55, 60, 70, 80, 95 ]
    max_size = 20
    category = 'american' #canadian, british, british_z
    subcategories = [
        # 'abbreviations',
        # 'contractions',
        'proper-names',
        'upper',
        'words',
    ]
    for size in sizes:
        if size > max_size:
            break
        for subcategory in subcategories:
            addFileToTrie(rootNode,
                'scowl_word_lists/english-%s.%i' % (subcategory, size),
                size, subcategory)
            addFileToTrie(rootNode,
                'scowl_word_lists/%s-%s.%i' % (category, subcategory, size),
                size, subcategory)
    return rootNode

def doLookup(rootNode, node, chars, wilds, foundWordSets, wordSet):
    for word in node.getWords():
        doLookup(rootNode, rootNode, chars, wilds, foundWordSets, wordSet | set([word]))

    if len(chars) == 0:
        if len(wordSet) > 0:
            foundWordSets.add(frozenset(wordSet))
        return

    if wilds > 0:
        for n in node.getChildren():
            doLookup(rootNode, n, list(chars), wilds - 1, foundWordSets, wordSet)

    char = chars.pop()

    # This allows finding matches that ignore a character
    doLookup(rootNode, node, list(chars), wilds, foundWordSets, wordSet)

    node = node.getChild(char)
    doLookup(rootNode, node, chars, wilds, foundWordSets, wordSet)

def lookup(rootNode, searchWord):
    print 'Looking up "%s"...' % (searchWord)
    wilds = 0
    for char in searchWord:
        if char == '.':
            wilds += 1
    chars = wordToChars(searchWord)
    chars.reverse()
    foundWordSets = set()
    doLookup(rootNode, rootNode, chars, wilds, foundWordSets, frozenset())
    return foundWordSets

def printWords(foundWordSets):
    l = list(foundWordSets)
    l.sort(key=calcWordSetWeight, reverse=True)
    for wordSet in l:
        print "%i:" % calcWordSetWeight(wordSet),
        for word in wordSet:
            print word,
        print

trie = buildTrie()
print "Built %i nodes for %i words" % (nodeCount, wordCount)

parser = argparse.ArgumentParser(description="Anagram finder")
# parser.add_argument('--foo', help='foo help')
parser.add_argument("searchString")
args = parser.parse_args()

if args.searchString:
    printWords(lookup(trie, args.searchString))
else:
    while True:
        try:
            searchWord = raw_input('Search input: ')
        except EOFError as e:
            break
        printWords(lookup(trie, searchWord))
