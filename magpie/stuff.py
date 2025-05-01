import itertools
from collections import defaultdict
from functools import cache
import re

ROW = ["[nt]", "h", "[ne]", "[ia]", "[ni]", "[ta]", "[un]", "[ac]", "[e]", "[e]"]


@cache
def get_regexp_for_length(length: int, reverse):
    if reverse:
        info = list(itertools.batched(reversed(ROW), 2))
    else:
        info = list(itertools.batched(ROW, 2))
    result = []
    for i in range(length // 3):
        left, right = info[i]
        result += f'(.{left}{right}|{left}.{right}|{left}{right}.)'
    if length % 3 == 0:
        pass
    elif length % 3 == 1:
        result += '.'
    else:
        left, right = info[length // 3]
        result += f'({left}.|.{left})'
    return re.compile(''.join(result))

def run(reverse=False):
    corpus = "../misc/words2.txt"
    result = defaultdict(list)
    with open(corpus, 'r') as file:
        for word in file.readlines():
            word = word.strip()
            if 6 <= len(word) <= 15:
                pattern = get_regexp_for_length(len(word), reverse)
                word2 = word[::-1] if reverse else word
                if pattern.match(word2):
                    result[len(word)].append(word)
    for l in range(5, 15):
        for item in result[l]:
            print(item)


run(False)
run(True)
