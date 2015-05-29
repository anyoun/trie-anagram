import sys, os

# path = '/Users/willt/Dropbox/Programming/anagram/scowl-2015.05.18/final/american-words.10'
path = 'american-words.txt'

global nodeCount, wordCount
nodeCount = 0
wordCount = 0

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
    def addWord(self, word):
        self.words.append(word)
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

def buildTrie():
    rootNode = TrieNode()
    f = open(path, 'r')
    for line in f:
        node = rootNode
        word = line.strip()
        if '\'' in word:
            continue
        for char in word:
            node = node.getChild(char)
        node.addWord(word)
        global wordCount
        wordCount += 1
    return rootNode

def lookup(rootNode):
    pass

print buildTrie().toString()
print "Built %i nodes for %i words" % (nodeCount, wordCount)
