from collections import Counter

import numpy as np

class X:
    string: str
    array: np.ndarray

    def __init__(self, value=''):
        if isinstance(value, str):
            self.string = value
            self.array = self.string_to_np(value)
        elif isinstance(value, np.ndarray):
            self.string = self.np_to_string(value)
            self.array = value[:]
        else:
            assert False

    def __add__(self, other):
        if not isinstance(other, X):
            other = X(other)
        if len(self.string) == 0:
            return other
        total = self.array + other.array - 1
        return X(total)

    def __sub__(self, other):
        if not isinstance(other, X):
            other = X(other)
        if len(self.string) == 0:
            return other
        total = self.array - other.array + 1
        return X(total)

    def __repr__(self):
        return '< "' + self.string + '" >'

    @staticmethod
    def string_to_np(string):
        result = [ord(x) - ord('A') + 1 for x in string.upper()]
        return np.array(result)

    @staticmethod
    def np_to_string(array):
        result = [chr(ord('A') + (item - 1) % 26) for item in list(array)]
        return ''.join(result)


def run():
    words = set()
    with open("../misc/words.txt") as file:
        for word in file:
            word = word.strip()
            if all(x.isalpha() for x in word):
                words.add(word.lower())
    across = X("escortfunnelquartztuckersecretcombed")
    down = X("egspfsrupaeiasacrishrkrpeeeeeeddddtd")
    for word in words:
        if len(word) ==  6:
            secret1 = word * 6
            secret2 = ''.join(x * 6 for x in word)
            result1 = across + secret1
            result2 = down + secret2
            count = sum(x == y for x, y in zip(result1.string, result2.string))
            if count > 15:
                print(word, count, result1, result2)

WORD1 = ["ESCORT", "FUNNEL", "QUARTZ", "TUCKER", "SECRET", "COMBED"]
WORD2 = ["ERASED", "GUSHED", "SPARED", "PACKED", "FERRET", "SWIPED"]

def run2():
    key = 'SECRET'
    crypt1 = [(X(word) + ch).string for word, ch in zip(WORD1, key)]
    crypt2a = [(X(word) + ch).string for word, ch in zip(WORD2, key)]
    crypt2 =[''.join(item) for item in zip(*crypt2a)]
    assert crypt1 == crypt2

    for i in range(6):
        print(f'{WORD1[i]} + {key[i] * 6} = {"".join(WORD2[j][i] for j in range(6))} + {key}'
              f'= {crypt2[i]}')

    counter = Counter(''.join(crypt2))
    print(counter.most_common())




if __name__ == '__main__':
    run2()

"""


EGSPFS
ILGRVZ
TLTVKB
WLVOVT
VVVVVV
BBBBRB

"""

def closestAge(lst, K):
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - K))]
    return lst[min(range(len(lst)), key=lambda i: abs(lst[i] - J))]

