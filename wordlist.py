import os
import config

def withAllFiles(func):
    sizes = [ 10, 20, 35, 40, 50, 55, 60, 70, 80, 95 ]
    for size in sizes:
        if size > config.Settings.max_size:
            break
        for category in config.Settings.categories:
            for subcategory in config.Settings.subcategories:
                filePath = 'scowl_word_lists/%s-%s.%i' % (category, subcategory, size)
                if os.path.exists(filePath):
                    f = open(filePath, 'r')
                    func(f, category, subcategory, size)
