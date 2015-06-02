import unittest
import anagram

class TestAnagrams(unittest.TestCase):
    def setUp(self):
        self.trie = anagram.buildTrie()

    def assertLookup(self, searchText, someMatch):
        foundWordSets = anagram.lookup(self.trie, searchText)
        stringSets = set()
        for wordSet in foundWordSets:
            s = ""
            for word in wordSet:
                if s != "": s += " "
                s += word.word
            stringSets.add(s)
        self.assertIn(someMatch, stringSets)

    def test_single_words(self):
        self.assertLookup('book', 'book')
        self.assertLookup('room', 'room')
        self.assertLookup('dirty', 'dirty')
        self.assertLookup('mayor', 'mayor')
        # self.assertLookup('clark', 'clark')
        self.assertLookup('dormitory', 'dirty room')
        # self.assertLookup('mayorclark', 'mayor clark')

if __name__ == '__main__':
    unittest.main()
