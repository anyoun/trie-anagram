
import sys, os, readline, argparse


class Config:
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

class Word:
    def __init__(self, word, frequency, subcategory):
        self.word = word
        self.frequency = frequency
        self.subcategory = subcategory
    def __str__(self):
        return '%s (%i%% %s)' % (self.word, self.frequency, self.subcategory)
    def weight(self):
        return len(self.word) * 10 + self.frequency / 10

class TrieNode(object):
    def __init__(self):
        super(TrieNode, self).__init__()
        self.children = { }
        self.words = [ ]
        Stats.nodeCount += 1
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
            s += " " + str(word)
        return s

def calcWordSetWeight(wordSet):
    return sum(map(lambda w: w.weight(), wordSet)) * len(wordSet)

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

def doLookup(rootNode, node, charNode, wilds, foundWordSets, wordSet):
    for word in node.getWords():
        newWordSet = wordSet | set([word])
        if Config.traceLookup: print "Found: %s" % (word)
        doLookup(rootNode, rootNode, charNode, wilds, foundWordSets, newWordSet)

    if charNode == None:
        if Config.traceLookup: print "No characters left, terminating with %i word sets" % (len(wordSet))
        if len(wordSet) > 0:
            foundWordSets.add(frozenset(wordSet))
        return

    if wilds > 0:
        if Config.traceLookup: print "Using a wildcard to search all children..."
        for n in node.getChildren():
            doLookup(rootNode, n, charNode, wilds - 1, foundWordSets, wordSet)

    char = charNode.char
    charNode = charNode.next

    if Config.traceLookup: print "Searching by skipping %s ..." % (char)
    doLookup(rootNode, node, charNode, wilds, foundWordSets, wordSet)

    node = node.getChild(char)
    if Config.traceLookup: print "Searching by using %s ..." % (char)
    doLookup(rootNode, node, charNode, wilds, foundWordSets, wordSet)

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Anagram finder")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument('--dump', action='store_true', help='Dump out entire search trie')
    grp.add_argument("--search")
    grp.add_argument("-i", "--interactiveSearch", action='store_true')
    args = parser.parse_args()

    trie = buildTrie()
    print "Built %i nodes for %i words" % (Stats.nodeCount, Stats.wordCount)

    if args.dump:
        print trie.toString()
    elif args.search:
        printWords(lookup(trie, args.search))
    elif args.interactiveSearch:
        while True:
            try:
                searchWord = raw_input('Search input: ')
            except EOFError as e:
                break
            printWords(lookup(trie, searchWord))
