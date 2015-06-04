# Optimization: Memoize search on trie nodes based on wilds/left/skipped
# What about sorting by character frequency?

import sys, os, readline, argparse


class Config:
    includePartialMatches = False
    traceLookup = False
    max_size = 20
    categories = [
        'english', #Base category
        'american',
        #'canadian',
        #'british',
        #'british_z',
    ]
    subcategories = [
        # 'abbreviations',
        # 'contractions',
        'proper-names',
        'upper',
        'words',
    ]

class Stats:
    nodeCount = 0
    wordCount = 0

class Filtering:
    allowed_one_letter = set([
        'a',
        'i',
    ])
    allowed_two_letter = set([
        'ah',
        'al',
        'by',
        'de',
        'do',
        'ex',
        'em',
        'en',
        'hi',
        'ha',
        'ho',
        'if',
        'in',
        'is',
        'it',
        'ma',
        'my',
        'oh',
        'on',
        'or',
        'ox',
        'un',
        'us',
        'we',
    ])

class CharNode:
    def __init__(self, char, next):
        self._char = char
        self._next = next
    @property
    def char(self):
        return self._char
    @property
    def next(self):
        return self._next
    def __str__(self):
        x = self
        s = ""
        while x != None:
            s += x.char
            x = x.next
        return s

class Word:
    def __init__(self, word, frequency, subcategory):
        self.word = word
        self.frequency = frequency
        self.subcategory = subcategory
    def __str__(self):
        return '%s (%i%% %s)' % (self.word, self.frequency, self.subcategory)
    @property
    def weight(self):
        return len(self.word) * 10 + self.frequency / 10

class TrieNode(object):
    def __init__(self):
        super(TrieNode, self).__init__()
        self._children = { }
        self._words = set()
        Stats.nodeCount += 1
    def getChild(self, char):
        if char not in self._children:
            n = TrieNode()
            self._children[char] = n
            return n
        else:
            return self._children[char]
    @property
    def children(self):
        return self._children.values()
    def addWord(self, word, frequency, subcategory):
        self._words.add(Word(word, frequency, subcategory))
    @property
    def words(self):
        return self._words
    def toString(self, indent = 0):
        s = "{ "
        for char,node in self._children.items():
            s += "\n%s%s: %s" % (' '*indent, char, node.toString(indent+1))
        s += " }"
        for word in self.words:
            s += " " + str(word)
        return s

def calcWordSetLength(wordSet):
    return sum(map(lambda w: len(w.word), wordSet))

def calcWordSetWeight(wordSet):
    return sum(map(lambda w: w.weight, wordSet)) / len(wordSet)

def sortChars(charList):
    charList.sort()

def wordToChars(word):
    word = word.strip().strip('.').lower()
    # chars = [x for x in word]
    chars = list(word)
    sortChars(chars)
    return chars

def addFileToTrie(rootNode, filePath, frequency, subcategory):
    if not os.path.exists(filePath):
        return
    f = open(filePath, 'r')
    for line in f:
        node = rootNode
        word = line.strip().lower()
        if '\'' in word or \
            (len(word) == 1 and word not in Filtering.allowed_one_letter) or \
            (len(word) == 2 and word not in Filtering.allowed_two_letter):
            continue
        for char in wordToChars(word):
            node = node.getChild(char)
        node.addWord(word, frequency, subcategory)
        Stats.wordCount += 1
    return rootNode

def buildTrie():
    rootNode = TrieNode()
    sizes = [ 10, 20, 35, 40, 50, 55, 60, 70, 80, 95 ]
    for size in sizes:
        if size > Config.max_size:
            break
        for category in Config.categories:
            for subcategory in Config.subcategories:
                addFileToTrie(rootNode,
                    'scowl_word_lists/%s-%s.%i' % (category, subcategory, size),
                    size, subcategory)
    return rootNode

def combineSortChars(x, y):
    allList = []
    while x != None:
        allList.append(x.char)
        x = x.next
    while y != None:
        allList.append(y.char)
        y = y.next
    sortChars(allList)
    allList.reverse()
    outputNode = None
    for char in allList:
        outputNode = CharNode(char, outputNode)
    return outputNode

def doLookup(rootNode, node, charNode, skippedNode, wilds, foundWordSets, wordSet, depth):
    for word in node.words:
        newWordSet = wordSet | set([word])
        newCharNode = combineSortChars(charNode, skippedNode)
        if Config.traceLookup: print "%sFound: %s (already %s), continuing with %s" % (depth*" ", word, wordSet, newCharNode)
        doLookup(rootNode, rootNode, newCharNode, None, wilds, foundWordSets, newWordSet, depth+1)

    if wilds > 0:
        if Config.traceLookup: print "%sUsing a wildcard to search all children..." % (depth*" ")
        for n in node.children:
            doLookup(rootNode, n, charNode, skippedNode, wilds-1, foundWordSets, wordSet, depth+1)

    if charNode == None:
        if Config.traceLookup: print "%sNo characters left, terminating with %i word sets" % (depth*" ", len(wordSet))
        if len(wordSet) > 0:
            foundWordSets.add(frozenset(wordSet))
        return

    char = charNode.char
    charNode = charNode.next

    if Config.traceLookup: print "%sSearching by skipping %s, %s left, %s skipped" % (depth*" ", char, charNode, CharNode(char, skippedNode))
    doLookup(rootNode, node, charNode, CharNode(char, skippedNode), wilds, foundWordSets, wordSet, depth+1)

    node = node.getChild(char)
    if Config.traceLookup: print "%sSearching by using %s. %s left, %s skipped" % (depth*" ", char, charNode, skippedNode)
    doLookup(rootNode, node, charNode, skippedNode, wilds, foundWordSets, wordSet, depth+1)

def lookup(rootNode, searchWord):
    # print 'Looking up "%s"...' % (searchWord)
    wilds = 0
    for char in searchWord:
        if char == '.':
            wilds += 1
    chars = None
    reversedChars = wordToChars(searchWord)
    reversedChars.reverse()
    for ch in reversedChars:
        chars = CharNode(ch, chars)
    foundWordSets = set()
    doLookup(rootNode, rootNode, chars, None, wilds, foundWordSets, frozenset(), 0)
    return foundWordSets

def printWords(foundWordSets, expectedLength):
    l = list(foundWordSets)
    l.sort(key=calcWordSetWeight, reverse=True)
    for wordSet in l:
        if not Config.includePartialMatches and calcWordSetLength(wordSet) < expectedLength:
            continue
        print "%i:" % calcWordSetWeight(wordSet),
        for word in wordSet:
            print word,
        print

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Anagram finder")
    parser.add_argument('-p', '--includePartialMatches', action='store_true')
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument('--dump', action='store_true', help='Dump out entire search trie')
    grp.add_argument("--search")
    grp.add_argument("-i", "--interactiveSearch", action='store_true')
    args = parser.parse_args()

    Config.includePartialMatches = args.includePartialMatches

    trie = buildTrie()
    print "Built %i nodes for %i words" % (Stats.nodeCount, Stats.wordCount)

    if args.dump:
        print trie.toString()
    elif args.search:
        printWords(lookup(trie, args.search), len(args.search))
    elif args.interactiveSearch:
        while True:
            try:
                searchWord = raw_input('Search input: ')
            except EOFError as e:
                break
            printWords(lookup(trie, searchWord), len(searchWord))
