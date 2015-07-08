import config, wordlist, string

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
        self._memoizedLookups = { }
        config.Stats.nodeCount += 1
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
        self._memoizedLookups = {}
        for child in self._children.values():
            child.clearMemoized()

def wordToChars(word):
    word = word.strip().strip('.').lower()
    chars = list(word)
    sortChars(chars)
    return chars

def wordSetsToStr(wordSets):
    s = "["
    for ws in wordSets:
        s += "("
        s += string.join([str(w.word) for w in ws], ", ")
        s += ")"
    s += "]"
    return s

def sortChars(charList):
    if config.Settings.sortCharactersByFrequency:
        charList.sort(key=lambda c: config.Stats.letterCounts.get(c, 0))
    else:
        charList.sort()

def addFileToTrie(rootNode, f, frequency, subcategory):
    for line in f:
        node = rootNode
        word = line.strip().lower()
        if config.Filtering.allowWord(word):
            for char in wordToChars(word):
                node = node.getOrCreateChild(char)
            node.addWord(word, frequency, subcategory)
            config.Stats.wordCount += 1
    return rootNode

def buildTrie():
    rootNode = TrieNode()
    wordlist.withAllFiles(buildFrequency)
    wordlist.withAllFiles(lambda f,cate,sub,size: addFileToTrie(rootNode, f, size, sub))
    return rootNode

def buildFrequency(f, category, subcategory, size):
    for line in f:
        word = line.strip().lower()
        if config.Filtering.allowWord(word):
            for char in wordToChars(word):
                if config.Settings.sortCharactersByFrequency:
                    config.Stats.letterCounts[char] = config.Stats.letterCounts.get(char, 0) + 1
