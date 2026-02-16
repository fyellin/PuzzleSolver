import itertools
import operator
from collections import defaultdict
from collections.abc import Sequence, Iterator, Iterable, Callable

from typing import Any

from sortedcontainers import SortedDict, SortedSet

from misc.primes import PRIMES
from solver import Clue, Clues, ConstraintSolver, ClueValueGenerator, KnownClueDict


class MyString(str):
    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.value}[{self.start}-{self.end}]'

    def __new__(cls, value: int, start: int, end: int) -> Any:
        return super().__new__(cls, value)  # type: ignore

    def __init__(self, value: int, start: int, end: int) -> None:
        super().__init__()
        self.value = value
        self.start = start
        self.end = end

    def delta(self):
        return self.end - self.start + 1

    def __eq__(self, other) -> bool:
        return other is not None and (self.value, self.start) == (other.value, other.start)

    def __hash__(self) -> int:
        return hash((self.value, self.start, self.end))

    def __lt__(self, other) -> bool:
        return (self.value, self.start) < (other.value, other.start)


def build_sequence_list(op: Callable[[int, int], int]) -> SortedDict:
    result = defaultdict(list)
    for start in range(1, 100_000):
        value = start
        for end in itertools.count(start + 1):
            value = op(value, end)
            if value >= 100_000:
                break
            result[value].append((start, end))
    return SortedDict(result)


PRODUCT_LIST = build_sequence_list(operator.mul)
SUM_LIST = build_sequence_list(operator.add)


def get_down_generator(brackets: int | None = None, item: int | None = None) -> ClueValueGenerator:
    def generator(clue: Clue) -> Iterator[str]:
        length = clue.length
        for value in SUM_LIST.irange(10 ** (length - 1), 10 ** length - 1):
            sums = SUM_LIST[value]
            if brackets is not None and len(sums) != brackets:
                continue
            if item is not None and not any(end - start + 1 == item for start, end in sums):
                continue
            yield value
    return generator


def across_generator(clue: Clue):
    length = clue.length
    for value in PRODUCT_LIST.irange(10 ** (length - 1), 10 ** length - 1):
        for start, end in PRODUCT_LIST[value]:
            yield MyString(value, start, end)


def across_generator_7a(_clue: Clue) -> Iterator[MyString]:
    def inner(start_index: int, product: int, count: int) -> Iterable[int]:
        if count == 0:
            if product >= 10_000 and product in PRODUCT_LIST:
                yield product
            return
        for index in itertools.count(start_index):
            value = product * PRIMES[index]
            if value >= 100_000:
                break
            yield from inner(index + 1, value, count - 1)

    return (MyString(value, start, end)
            for value in SortedSet(inner(0, 1, 5))
            for start, end in PRODUCT_LIST[value])

GRID = """
XXXX.
.X..X
X..X.
XX...
X....
"""

ACROSSES = [
    (1, 5, across_generator),
    (5, 4, across_generator),
    (7, 5, across_generator_7a),
    (9, 4, across_generator),
    (11, 5, across_generator),
]

DOWNS = [
    (1, 4, get_down_generator(7, 61)),
    (2, 3, get_down_generator()),
    (3, 5, get_down_generator()),
    (4, 2, get_down_generator(3, None)),
    (6, 4, get_down_generator(15, 4)),
    (8, 3, get_down_generator(1, 32)),
    (10, 2, get_down_generator(1, None))
]


class Magpie223 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie223()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True, max_debug_depth=50)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)
        self.add_all_constraints()

    @staticmethod
    def get_clues() -> Sequence[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length, generator in information:
                clue = Clue(f'{number}{letter}', is_across, grid[number - 1], length, generator=generator)
                clues.append(clue)
        return clues

    def add_all_constraints(self) -> None:
        def different_length(a: MyString, b: MyString):
            return a.end - a.start != b.end - b.start

        for clue1, clue2 in itertools.combinations(self._clue_list, 2):
            if clue1.is_across and clue2.is_across:
                self.add_constraint((clue1, clue2), different_length)

    def plot_board(self, clue_values: KnownClueDict | None = None, **more_args: Any) -> None:
        special = int(clue_values[self.clue_named('3d')])
        sequences = len(SUM_LIST[special])
        subtext = f'[{sequences}]'
        super().plot_board(clue_values, subtext=subtext, **more_args)


if __name__ == '__main__':
    Magpie223.run()

