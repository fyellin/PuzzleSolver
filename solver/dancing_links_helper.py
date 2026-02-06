from __future__ import annotations

import string
from functools import cache
from itertools import combinations, count
from typing import Protocol, Sequence

import math


class _Orderer(Protocol):
    def left(self, i: int) -> set[str | tuple[str, str]]: ...
    def right(self, i: int) -> set[str | tuple[str, str]]: ...
    def all_codes(self) -> set[str]: ...


class OrdererLessEqual(_Orderer):
    prefix: str

    def __init__(self, prefix, count):
        self.count = count
        self.prefix = prefix

    @cache
    def left(self, i) -> set[str]:
        t = i
        result = set()
        while t > 0:
            result.add(f'{self.prefix}:{t}')
            t &= t - 1
        return result

    @cache
    def right(self, i) -> set[str]:
        t = i + 1
        result = set()
        while t < self.count:
            result.add(f'{self.prefix}:{t}')
            t += (t & -t)
        return result

    def all_codes(self) -> set[str]:
        return {f'{self.prefix}:{t}' for t in range(1, self.count)}


class OrdererLessThan (OrdererLessEqual):
    def __init__(self, prefix: str, count: int):
        super().__init__(prefix, count + 1)

    def left(self, i) -> set[str]:
        return super().left(i + 1)


class OrdererEqual(_Orderer):
    def __init__(self, prefix: str, _count: int):
        # We use a single element with coloring.
        self.code = f'{prefix}:0'

    def left(self, i):
        return {(self.code, str(i))}

    def right(self, i):
        return {(self.code, str(i))}

    def all_codes(self):
        return {self.code}


def test_orderer(count):
    order = OrdererEqual("x", count)
    result = [(i, j)
              for i in range(count) for j in range(count)
              if order.left(i).isdisjoint(order.right(j)) != (i == j)]
    print(order.all_codes())
    return result


class Orderer:
    LT = OrdererLessThan
    LE = OrdererLessEqual
    EQ = OrdererEqual


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

    def locator(self, location: tuple[int, int], is_across: bool):
        row, column = location
        return f'{self.prefix}r{row}c{column}-{"A" if is_across else "D"}'
