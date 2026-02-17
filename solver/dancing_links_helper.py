from __future__ import annotations

import math
import string
from collections.abc import Hashable, Sequence
from functools import cache
from itertools import combinations, count


class _Orderer_LT_LE[T: Hashable]:  # noqa
    def __init__(self, prefix: str, count_or_items: int | set[T], is_lt: bool) -> None:
        self._prefix = prefix
        self._is_lt = is_lt
        if isinstance(count_or_items, int):
            self._mapping = None
            count = count_or_items
        else:
            self._mapping = {value: i for i, value in enumerate(sorted(count_or_items))}
            count = len(count_or_items)
        self._count = count
        self._real_count = count + int(is_lt)

    @cache
    def left(self, i: int | T) -> set[str]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")
        t = int(i) + int(self._is_lt)
        result = set()
        while t > 0:
            result.add(f'{self._prefix}:{t}')
            t &= t - 1
        return result

    @cache
    def right(self, i: int | T) -> set[str]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")
        t = i + 1
        result = set()
        while t < self._real_count:
            result.add(f'{self._prefix}:{t}')
            t += (t & -t)
        return result

    def all_codes(self) -> set[str]:
        return {f'{self._prefix}:{t}' for t in range(1, self._real_count)}


class OrdererLessEqual[T: Hashable](_Orderer_LT_LE):
    def __init__(self, prefix: str, count_or_items: int | set[T]) -> None:
        super().__init__(prefix, count_or_items, is_lt=False)


class OrdererLessThan[T: Hashable](_Orderer_LT_LE):
    def __init__(self, prefix: str, count_or_items: int | set[T]) -> None:
        super().__init__(prefix, count_or_items, is_lt=True)


class OrdererEqual[T: Hashable]:
    def __init__(self, prefix: str, count_or_items: int | set[T]):
        # We use a single element with coloring.
        self.code = f'{prefix}:0'
        if isinstance(count_or_items, int):
            self._mapping = None
            self._count = count_or_items
        else:
            self._mapping = {value: i for i, value in enumerate(sorted(count_or_items))}
            self._count = len(count_or_items)

    def left(self, i: int | T) -> set[tuple[str, str]]:
        if self._mapping:
            i = self._mapping[i]
        else:
            if not (0 <= i < self._count):
                raise ValueError(f"index {i} out of range [0, {self._count})")

        return {(self.code, str(i))}

    def right(self, i: int | T) -> set[tuple[str, str]]:
        if self._mapping:
            i = self._mapping[i]
        return {(self.code, str(i))}

    def all_codes(self) -> set[str]:
        return {self.code}


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

    def locator(self, location: tuple[int, int], is_across: bool) -> str:
        row, column = location
        return f'{self.prefix}r{row}c{column}-{"A" if is_across else "D"}'


class TestAllOrders:
    @staticmethod
    def _check_lt_le(orderer, count: int, is_lt: bool):
        for a in range(count):
            for b in range(count):
                disjoint = orderer.left(a).isdisjoint(orderer.right(b))
                expected = (a < b) if is_lt else (a <= b)
                assert disjoint == expected, f"a={a}, b={b}"
        all_used = (set().union(*(orderer.left(i) for i in range(count))) |
                    set().union(*(orderer.right(i) for i in range(count))))
        assert orderer.all_codes() == all_used

    def test_lt_int(self):
        self._check_lt_le(Orderer.LT("x", 6), 6, is_lt=True)

    def test_le_int(self):
        self._check_lt_le(Orderer.LE("x", 6), 6, is_lt=False)

    def test_lt_set(self):
        items = {'p', 'q', 'r', 's'}
        orderer = Orderer.LT("x", items)
        sorted_items = sorted(items)
        for a, va in enumerate(sorted_items):
            for b, vb in enumerate(sorted_items):
                disjoint = orderer.left(va).isdisjoint(orderer.right(vb))
                assert disjoint == (a < b), f"left({va}) disjoint right({vb})"

    def test_le_set(self):
        items = {'p', 'q', 'r', 's'}
        orderer = Orderer.LE("x", items)
        sorted_items = sorted(items)
        for a, va in enumerate(sorted_items):
            for b, vb in enumerate(sorted_items):
                disjoint = orderer.left(va).isdisjoint(orderer.right(vb))
                assert disjoint == (a <= b), f"left({va}) disjoint right({vb})"

    def test_lt_count_1(self):
        orderer = Orderer.LT("x", 1)
        assert not orderer.left(0).isdisjoint(orderer.right(0))

    def test_le_count_1(self):
        orderer = Orderer.LE("x", 1)
        assert orderer.left(0).isdisjoint(orderer.right(0))

    def test_eq_int(self):
        orderer = Orderer.EQ("e", 4)
        assert orderer.all_codes() == {orderer.code}
        for a in range(4):
            for b in range(4):
                (left_code, left_color) = next(iter(orderer.left(a)))
                (right_code, right_color) = next(iter(orderer.right(b)))
                assert left_code == right_code
                assert (left_color == right_color) == (a == b), f"a={a}, b={b}"

    def test_eq_set(self):
        items = {'x', 'y', 'z'}
        orderer = Orderer.EQ("e", items)
        for va in sorted(items):
            for vb in sorted(items):
                left_color = next(iter(orderer.left(va)))[1]
                right_color = next(iter(orderer.right(vb)))[1]
                assert (left_color == right_color) == (va == vb)


    def test_lt_out_of_bounds(self):
        import pytest
        orderer = Orderer.LT("x", 4)
        with pytest.raises(ValueError):
            orderer.left(-1)
        with pytest.raises(ValueError):
            orderer.left(4)
        with pytest.raises(ValueError):
            orderer.right(-1)
        with pytest.raises(ValueError):
            orderer.right(4)

    def test_le_out_of_bounds(self):
        import pytest
        orderer = Orderer.LE("x", 4)
        with pytest.raises(ValueError):
            orderer.left(-1)
        with pytest.raises(ValueError):
            orderer.left(4)
        with pytest.raises(ValueError):
            orderer.right(-1)
        with pytest.raises(ValueError):
            orderer.right(4)

    def test_eq_out_of_bounds(self):
        import pytest
        orderer = Orderer.EQ("e", 4)
        with pytest.raises(ValueError):
            orderer.left(-1)
        with pytest.raises(ValueError):
            orderer.left(4)

    def test_lt_missing_key(self):
        import pytest
        orderer = Orderer.LT("x", {'a', 'b', 'c'})
        with pytest.raises(KeyError):
            orderer.left('z')
        with pytest.raises(KeyError):
            orderer.right('z')

    def test_le_missing_key(self):
        import pytest
        orderer = Orderer.LE("x", {'a', 'b', 'c'})
        with pytest.raises(KeyError):
            orderer.left('z')
        with pytest.raises(KeyError):
            orderer.right('z')

    def test_eq_missing_key(self):
        import pytest
        orderer = Orderer.EQ("e", {'a', 'b', 'c'})
        with pytest.raises(KeyError):
            orderer.left('z')


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, "-v"])
