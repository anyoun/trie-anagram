import sys, os, readline, argparse
import config, wordlist, trie

def calcWordSetLength(wordSet):
    return sum(map(lambda w: len(w.word), wordSet))

def calcWordSetWeight(wordSet):
    return sum(map(lambda w: w.weight, wordSet)) / len(wordSet)

def combineSortChars(x, y):
    allList = []
    while x != None:
        allList.append(x.char)
        x = x.next
    while y != None:
        allList.append(y.char)
        y = y.next
    trie.sortChars(allList)
    allList.reverse()
    outputNode = None
    for char in allList:
        outputNode = trie.CharNode(char, outputNode)
    return outputNode

def doLookup(rootNode, node, charNode, skippedNode, wilds, currentWordSets, depth):
    originalNode = node
    remainingStr = ""
    skippedStr = ""
    foundWordSets = set()
    if config.Settings.memoize:
        remainingStr = combineSortChars(charNode, skippedNode)
        for memo in originalNode.memoizedLookups:
            if remainingStr == memo.remainingStr and memo.wilds == wilds:
                for cws in currentWordSets:
                    for mws in memo.wordSets:
                        fullWordSet = cws | mws
                        if len(fullWordSet) > 0:
                            foundWordSets.add(fullWordSet)
                return frozenset(foundWordSets)

    if node and node.words:
        newCurrentWordSets = []
        newCharNode = combineSortChars(charNode, skippedNode)
        for cws in currentWordSets:
            for word in node.words:
                newCurrentWordSets.append(cws.union([word]))
                if config.Settings.traceLookup: print "%sFound: %s (already %s), continuing with %s" % (depth*" ", word, cws, newCharNode)
        foundWordSets.update(doLookup(rootNode, rootNode, newCharNode, None, wilds, newCurrentWordSets, depth+1))

    if wilds > 0:
        if Config.traceLookup: print "%sUsing a wildcard to search all children..." % (depth*" ")
        for n in node.children:
            foundWordSets.update(doLookup(rootNode, n, charNode, skippedNode, wilds-1, currentWordSets, depth+1))

    if node == None or charNode == None:
        if config.Settings.traceLookup: print "%sNo characters or children left, terminating with %i word sets" % (depth*" ", len(currentWordSets))
        for cws in currentWordSets:
            if len(cws) > 0:
                foundWordSets.add(cws)
    else:
        char = charNode.char
        charNode = charNode.next

        if config.Settings.traceLookup: print "%sSearching by skipping %s, %s left, %s skipped" % (depth*" ", char, charNode, CharNode(char, skippedNode))
        foundWordSets.update(doLookup(rootNode, node, charNode, trie.CharNode(char, skippedNode), wilds, currentWordSets, depth+1))

        node = node.getChild(char)
        if node:
            if config.Settings.traceLookup: print "%sSearching by using %s. %s left, %s skipped" % (depth*" ", char, charNode, skippedNode)
            foundWordSets.update(doLookup(rootNode, node, charNode, skippedNode, wilds, currentWordSets, depth+1))

    if config.Settings.memoize:
        originalNode.memoizedLookups.append(MemorizedLookup(remainingStr, wilds, foundWordSets))
    return foundWordSets

class MemorizedLookup:
    def __init__(self, remainingStr, wilds, wordSets):
        self.remainingStr = remainingStr
        self.wilds = wilds
        self.wordSets = wordSets

def lookup(rootNode, searchWord):
    # print 'Looking up "%s"...' % (searchWord)
    wilds = 0
    for char in searchWord:
        if char == '.':
            wilds += 1
    chars = None
    reversedChars = trie.wordToChars(searchWord)
    reversedChars.reverse()
    for ch in reversedChars:
        chars = trie.CharNode(ch, chars)
    foundWordSets = doLookup(rootNode, rootNode, chars, None, wilds, [frozenset()], 0)
    if config.Settings.memoize:
        rootNode.clearMemoized()
    return foundWordSets

def printWords(foundWordSets, expectedLength):
    l = list(foundWordSets)
    l.sort(key=calcWordSetWeight, reverse=True)
    for wordSet in l:
        if not config.Settings.includePartialMatches and calcWordSetLength(wordSet) < expectedLength:
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

    config.Settings.includePartialMatches = args.includePartialMatches

    trieRoot = trie.buildTrie()
    print "Built %i nodes for %i words" % (config.Stats.nodeCount, config.Stats.wordCount)

    if args.dump:
        print trieRoot.toString()
    elif args.search:
        printWords(lookup(trieRoot, args.search), len(args.search))
    elif args.interactiveSearch:
        while True:
            try:
                searchWord = raw_input('Search input: ')
            except EOFError as e:
                break
            printWords(lookup(trieRoot, searchWord), len(searchWord))
