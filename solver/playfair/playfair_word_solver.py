import contextlib
import math
import pathlib
import re
from collections import Counter
from collections.abc import Sequence
from itertools import pairwise


class PlayfairEncoder:
    def __init__(self, key: str):
        self.key = key
        key = key.upper().replace("J", "I")
        letters = set(key)
        assert key.isalpha() and len(key) == len(letters), f"Bad keyword: {key}"
        other_letters = [x for x in 'ABCDEFGHIKLMNOPQRSTUVWXYZ' if x not in letters]
        self.box = key + ''.join(other_letters)

    def encode(self, word, delta=+1):
        word = word.replace("J", "I")
        if len(word) % 2:
            word += 'X'

        result = []
        for index in range(0, len(word), 2):
            char1, char2 = word[index], word[index + 1]
            r1, c1 = divmod(self.box.index(char1), 5)
            r2, c2 = divmod(self.box.index(char2), 5)
            if r1 == r2:
                if c1 != c2:
                    c1, c2 = (c1 + delta) % 5, (c2 + delta) % 5
            elif c1 == c2:
                r1, r2 = (r1 + delta) % 5, (r2 + delta) % 5
            else:
                c1, c2 = c2, c1
            result.append(self.box[5 * r1 + c1])
            result.append(self.box[5 * r2 + c2])
        return ''.join(result)

    def decode(self, word):
        return self.encode(word, -1)

    def __str__(self):
        return f"<Playfair '{self.key}'>"


def get_word_list():
    filename = pathlib.Path(__file__).parent / "../../misc/words2.txt"
    print(filename)
    with pathlib.Path(filename).open() as file:
        words = set(file.read().split())
    words = {x.upper().replace('-', '').replace("'", '').replace('J', 'I') for x in words}
    words = {x for x in words if re.fullmatch(r'[A-Z]*', x)}
    all_words = words
    words = {x for x in words if x.isalpha() and len(set(x)) == len(x)}
    return words, all_words


def main1():
    global result
    _phrase = "maysamenbufo".upper()
    _words, all_words = get_word_list()
    encoder = PlayfairEncoder("SHOCKUMENTARY")
    for word in sorted(all_words):
        if len(word) != 4:
            continue
        result = encoder.encode(word)
        if re.fullmatch(r'.AYS', result) and result in all_words:
            print(word, result)


def main3():
    encoder = PlayfairEncoder("BELOMANCY")
    for x in "ABCDEFGHIKLMNOPQRSTUVWXYZ":
        word = "RK" + x + "S"
        print(word, encoder.decode(word))


class Template:
    def __init__(self, text: str | Sequence[str]):
        table = Counter((i, j, k) for (i, j), (_, k) in pairwise(pairwise(text)))
        # table = Counter((i, j, k) for (i, j), (_, k) in pairwise(pairwise(text)))
        length = math.sqrt(sum(v * v for v in table.values()))
        self.table = table
        self.length = length

    def __matmul__(self, other):
        assert isinstance(other, Template)
        other_table = other.table
        total = sum(value * other_table.get(key, 0)
                    for key, value in self.table.items())
        return total / (self.length * other.length)


def main2():
    # url = "https://www.gutenberg.org/files/946/old/lsusn11.txt"
    # result = urlopen(url).read().decode("ASCII").upper().replace("J", "I")
    #
    file = "/users/fy/Desktop/text_fic.txt"
    with pathlib.Path(file).open() as f:
        result = f.read().upper().replace("J", "I")

    result = [x for x in result if x.isalpha()]
    english = Template(result)
    print(english.length, english @ english)
    phrase = "IBTH GYRK LQBY CKBX QOIL MCIE YTEM MIBI MVMG GOMH GYIE PAFA COEY".replace(" ", "")
    words = get_word_list()
    words = {x for x in words if len(x) == 9}
    results = []
    for word in sorted(words):
        decode = PlayfairEncoder(word).decode(phrase)
        delta = Template(decode) @ english
        results.append((delta, word, decode))
    results.sort(reverse=True)
    with pathlib.Path("/tmp/stuff.txt").open("w") as f:
        with contextlib.redirect_stdout(f):
            for delta, word, decode in results:
                print(word, decode, delta)


if __name__ == '__main__':
    main1()
