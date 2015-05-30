import sys, os, readline

# path = '/Users/willt/Dropbox/Programming/anagram/scowl-2015.05.18/final/american-words.10'
path = 'american-words.txt'

global nodeCount, wordCount
nodeCount = 0
wordCount = 0

class Word:
    def __init__(self, word, frequency, subcategory):
        self.word = word
        self.frequency = frequency
        self.subcategory = subcategory
    def __str__(self):
        return '%i %s (%s)' % (self.frequency, self.word, self.subcategory)

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
        # first = True
        for char,node in self.children.items():
            # if not first:
            #     s += ", "
            # first = False
            s += "\n%s%s: %s" % (' '*indent, char, node.toString(indent+1))
        s += " }"
        for word in self.words:
            s += " " + word
        return s

def wordToChars(word):
    word = word.strip().strip('.').lower()
    # chars = [x for x in word]
    chars = list(word)
    chars.sort() #What about sorting by character frequency?
    return chars

def addFileToTrie(rootNode, filePath, frequency, subcategory):
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
    max_size = 10
    category = 'american' #canadian, british, british_z
    subcategories = [
        # 'abbreviations',
        # 'contractions',
        # 'proper-names',
        # 'upper',
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

def doLookup(node, chars, wilds):
    words = set(node.getWords())

    if len(chars) == 0:
        return words

    if wilds > 0:
        for n in node.getChildren():
            words.update(doLookup(n, list(chars), wilds - 1))

    char = chars.pop()
    words.update(doLookup(node, list(chars), wilds))
    node = node.getChild(char)
    words.update(doLookup(node, chars, wilds))

    return words

def lookup(rootNode, searchWord):
    print 'Looking up "%s"...' % (searchWord)
    wilds = 0
    for char in searchWord:
        if char == '.':
            wilds += 1
    chars = wordToChars(searchWord)
    chars.reverse()
    return doLookup(rootNode, chars, wilds)

trie = buildTrie()
# print trie.toString()
print "Built %i nodes for %i words" % (nodeCount, wordCount)

while True:
    try:
        searchWord = raw_input('Search input: ')
    except EOFError as e:
        break
    for word in lookup(trie, searchWord):
        print word
