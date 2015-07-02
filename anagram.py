# Optimization: Memoize search
# To correctly memoize, doLookup needs to return all of the matches. This
#   might be multiple word lists. We'll need to add the already matched word
#   list on to this. We will no longer pass foundWordSets around through args.
# Can also memoize failure: If we've already searched with more skpped/missed/wilds
#   and that already failed, we can just stop now.
# Would it be faster to implement wilds by just generating all of the search
#   possibilities ahead of time? It should be the same amout of searching but
#   might increase the memoization hit rate for failures. Might decrease
#   hit rate for successes though.
# Multi-word searching doesn't work correctly with memoization. Needs to
#   return multiple word sets.

import sys, os, readline, argparse


class Config:
    traceLookup = False
    includePartialMatches = False
    sortCharactersByFrequency = True
    memoize = False
    max_size = 50
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

    letterCounts = { }

class Filtering:
    _allowed_one_letter = set([
        'a',
        'i',
    ])
    _allowed_two_letter = set([
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
    @classmethod
    def allowWord(self, word):
        return not ('\'' in word or \
            (len(word) == 1 and word not in self._allowed_one_letter) or \
            (len(word) == 2 and word not in self._allowed_two_letter))

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
        self._memoizedLookups = [ ]
        Stats.nodeCount += 1
    def getOrCreateChild(self, char):
        n = self._children.get(char)
        if not n:
            n = TrieNode()
            self._children[char] = n
        return n
    def getChild(self, char):
        return self._children.get(char)
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
    @property
    def memoizedLookups(self):
        return self._memoizedLookups
    def clearMemoized(self):
        self._memoizedLookups = []
        for child in self._children.values():
            child.clearMemoized()

def calcWordSetLength(wordSet):
    return sum(map(lambda w: len(w.word), wordSet))

def calcWordSetWeight(wordSet):
    return sum(map(lambda w: w.weight, wordSet)) / len(wordSet)

def sortChars(charList):
    if Config.sortCharactersByFrequency:
        charList.sort(key=lambda c: Stats.letterCounts.get(c, 0))
    else:
        charList.sort()

def wordToChars(word):
    word = word.strip().strip('.').lower()
    chars = list(word)
    sortChars(chars)
    return chars

def buildFrequency(f, category, subcategory, size):
    for line in f:
        word = line.strip().lower()
        if Filtering.allowWord(word):
            for char in wordToChars(word):
                if Config.sortCharactersByFrequency:
                    Stats.letterCounts[char] = Stats.letterCounts.get(char, 0) + 1

def addFileToTrie(rootNode, f, frequency, subcategory):
    for line in f:
        node = rootNode
        word = line.strip().lower()
        if Filtering.allowWord(word):
            for char in wordToChars(word):
                node = node.getOrCreateChild(char)
            node.addWord(word, frequency, subcategory)
            Stats.wordCount += 1
    return rootNode

def withAllFiles(func):
    sizes = [ 10, 20, 35, 40, 50, 55, 60, 70, 80, 95 ]
    for size in sizes:
        if size > Config.max_size:
            break
        for category in Config.categories:
            for subcategory in Config.subcategories:
                filePath = 'scowl_word_lists/%s-%s.%i' % (category, subcategory, size)
                if os.path.exists(filePath):
                    f = open(filePath, 'r')
                    func(f, category, subcategory, size)

def buildTrie():
    rootNode = TrieNode()
    withAllFiles(buildFrequency)
    withAllFiles(lambda f,cate,sub,size: addFileToTrie(rootNode, f, size, sub))
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

def doLookup(rootNode, node, charNode, skippedNode, wilds, foundWordSets, currentWordSets, depth):
    originalNode = node
    remainingStr = ""
    skippedStr = ""
    if Config.memoize:
        remainingStr = str(charNode)
        skippedStr = str(skippedNode)
        for memo in originalNode.memoizedLookups:
            if remainingStr == memo.remainingStr and skippedStr == memo.skippedStr and memo.wilds == wilds:
                for cws in currentWordSets:
                    for mws in memo.wordSets:
                        fullWordSet = cws | mws
                        if len(fullWordSet) > 0:
                            foundWordSets.add(fullWordSet)
                return #Early return since it's memoized

    if node and node.words:
        newCurrentWordSets = []
        newCharNode = combineSortChars(charNode, skippedNode)
        for cws in currentWordSets:
            for word in node.words:
                newCurrentWordSets.append(cws.union([word]))
                if Config.traceLookup: print "%sFound: %s (already %s), continuing with %s" % (depth*" ", word, cws, newCharNode)
        doLookup(rootNode, rootNode, newCharNode, None, wilds, foundWordSets, newCurrentWordSets, depth+1)
        # currentWordSets = newCurrentWordSets

    if wilds > 0:
        if Config.traceLookup: print "%sUsing a wildcard to search all children..." % (depth*" ")
        for n in node.children:
            doLookup(rootNode, n, charNode, skippedNode, wilds-1, foundWordSets, currentWordSets, depth+1)

    if node == None or charNode == None:
        if Config.traceLookup: print "%sNo characters or children left, terminating with %i word sets" % (depth*" ", len(currentWordSets))
        for cws in currentWordSets:
            if len(cws) > 0:
                foundWordSets.add(cws)
    else:
        char = charNode.char
        charNode = charNode.next

        if Config.traceLookup: print "%sSearching by skipping %s, %s left, %s skipped" % (depth*" ", char, charNode, CharNode(char, skippedNode))
        doLookup(rootNode, node, charNode, CharNode(char, skippedNode), wilds, foundWordSets, currentWordSets, depth+1)

        node = node.getChild(char)
        if node:
            if Config.traceLookup: print "%sSearching by using %s. %s left, %s skipped" % (depth*" ", char, charNode, skippedNode)
            doLookup(rootNode, node, charNode, skippedNode, wilds, foundWordSets, currentWordSets, depth+1)

    if Config.memoize:
        originalNode.memoizedLookups.append(MemorizedLookup(remainingStr, skippedStr, wilds, currentWordSets))

class MemorizedLookup:
    def __init__(self, remainingStr, skippedStr, wilds, wordSets):
        self.remainingStr = remainingStr
        self.skippedStr = skippedStr
        self.wilds = wilds
        self.wordSets = wordSets

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
    doLookup(rootNode, rootNode, chars, None, wilds, foundWordSets, [frozenset()], 0)
    if Config.memoize:
        rootNode.clearMemoized()
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
