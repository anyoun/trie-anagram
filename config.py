class Settings:
    traceLookup = False
    includePartialMatches = False
    sortCharactersByFrequency = True
    memoize = True
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
