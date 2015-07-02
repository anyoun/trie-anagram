import unittest
import anagram

from datetime import datetime

class TestAnagrams(unittest.TestCase):
    def setUp(self):
        startTime = datetime.now()
        self.trie = anagram.buildTrie()
        print "Build took %s" % (datetime.now() - startTime)

    def assertLookup(self, searchText, someMatch):
        foundWordSets = anagram.lookup(self.trie, searchText)
        stringSets = set()
        for wordSet in foundWordSets:
            s = ""
            sortedWords = list(wordSet)
            sortedWords.sort()
            for word in sortedWords:
                if s != "": s += " "
                s += word.word
            stringSets.add(s)
        self.assertIn(someMatch, stringSets)

    def test_single_words(self):
        startTime = datetime.now()
        self.assertLookup('my', 'my')
        self.assertLookup('book', 'book')
        self.assertLookup('room', 'room')
        self.assertLookup('dirty', 'dirty')
        self.assertLookup('mayor', 'mayor')
        self.assertLookup('clark', 'clark')
        print "single_words took %s" % (datetime.now() - startTime)

    def test_multiple_words(self):
        startTime = datetime.now()
        self.assertLookup('roommy', 'my room')
        self.assertLookup('dormitory', 'dirty room')
        self.assertLookup('mayorclark', 'mayor clark')
        print "multiple_words took %s" % (datetime.now() - startTime)

if __name__ == '__main__':
    unittest.main()
