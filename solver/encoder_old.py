import math
import string
from collections.abc import Sequence
from itertools import combinations, count


class Encoder:
    prefix: str
    alphabet: str
    table: dict[str, tuple[Sequence[int], Sequence[int]]]

    @staticmethod
    def of_alphabet(prefix: str = "") -> Encoder:
        return Encoder(string.ascii_uppercase, prefix)

    @staticmethod
    def digits(prefix: str = "") -> Encoder:
        return Encoder(string.digits, prefix)

    @staticmethod
    def of(alphabet: str, prefix: str = "") -> Encoder:
        return Encoder(alphabet, prefix)

    def __init__(self, alphabet: str, prefix: str = ""):
        self.alphabet = alphabet
        self.prefix = prefix
        size = next(i for i in count(2, 2)
                    if math.comb(i, i // 2) >= len(alphabet))
        self.table = {
            ch: (down, (*across, size + 1))
            for ch, across in zip(alphabet, combinations(range(size), size // 2))
            for down in [tuple(x for x in range(size) if x not in across)]
        }

    def encode(self, letter: str, location: tuple[int, int], is_across: bool
               ) -> Sequence[str]:
        row, column = location
        return [f'{self.prefix}r{row}c{column}-{value}'
                for value in self.table[letter][is_across]]

    def locator(self, location: tuple[int, int], is_across: bool) -> str:
        row, column = location
        return f'{self.prefix}r{row}c{column}-{"A" if is_across else "D"}'
