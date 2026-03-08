import itertools
import operator
from collections import defaultdict
from collections.abc import Callable, Iterator, Sequence
from typing import Unpack

from misc import prime_factors
from solver import (
    AbstractClueValue,
    Clue,
    Clues,
    ClueValue,
    ClueValueGenerator,
    ConstraintSolver,
    DrawGridKwargs,
    KnownClueDict,
)


class MyString(AbstractClueValue):
    """Across clue value: product digits plus run metadata; subtype of ``AbstractClueValue``."""

    __slots__ = ('value', 'start', 'end')

    def __init__(self, value: int, start: int, end: int) -> None:
        super().__init__(str(value))
        self.value = value
        self.start = start
        self.end = end

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f'{self.value}[{self.start}-{self.end}]'

    def delta(self) -> int:
        return self.end - self.start + 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MyString):
            return NotImplemented
        return (self.value, self.start, self.end) == (other.value, other.start, other.end)

    def __hash__(self) -> int:
        return hash((self.value, self.start, self.end))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MyString):
            return NotImplemented
        return (self.value, self.start) < (other.value, other.start)


def build_sequence_list(op: Callable[[int, int], int]
                        ) -> dict[int, dict[int, list[tuple[int, int]]]]:
    result = defaultdict(lambda: defaultdict(list))
    for start in itertools.count(1):
        if op(start, start + 1) >= 100_000:
            break
        value = start
        for end in itertools.count(start + 1):
            value = op(value, end)
            if value >= 100_000:
                break
            result[len(str(value))][value].append((start, end))
    return result


PRODUCT_LIST = build_sequence_list(operator.mul)
SUM_LIST = build_sequence_list(operator.add)


def get_down_generator(brackets: int | None = None, item: int | None = None
                       ) -> ClueValueGenerator:
    def generator(clue: Clue) -> Iterator[int]:
        for value, sums in SUM_LIST[clue.length].items():
            if brackets is not None and len(sums) != brackets:
                continue
            if item is not None and not any(
                    end - start + 1 == item for start, end in sums):
                continue
            yield value
    return generator


def across_generator(clue: Clue):
    for value, products in PRODUCT_LIST[clue.length].items():
        for start, end in products:
            yield MyString(value, start, end)


ACROSS_LENGTHS = "5/14/5/41/5"
DOWN_LENGTHS = "41/32/5/23/14"


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
        clue_map = Clues.clue_map_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        for (number, is_across), clue in clue_map.items():
            match number, is_across:
                case (1, False):
                    generator = get_down_generator(7, 61)
                case (4, False):
                    generator = get_down_generator(3, None)
                case (6, False):
                    generator = get_down_generator(15, 4)
                case (8, False):
                    generator = get_down_generator(1, 32)
                case (10, False):
                    generator = get_down_generator(1, None)
                case _:
                    generator = across_generator if is_across else get_down_generator()

            clue.generator = generator
        return list(clue_map.values())

    def add_all_constraints(self) -> None:
        for clue1, clue2 in itertools.combinations(self.clue_list, 2):
            if clue1.is_across and clue2.is_across:
                self.add_constraint((clue1, clue2), lambda a, b: a.delta() != b.delta())

        self.add_constraint("7a", self.has_five_prime_factors)

    def has_five_prime_factors(self, value: ClueValue) -> bool:
        value = int(value)
        if value % 4 == 0 or value % 9 == 9 or value % 25 == 0:
            return False
        f = prime_factors(value)
        return len(f) == 5 and all(p[1] == 1 for p in f)

    def plot_board(self,
                   clue_values: KnownClueDict | None = None,
                   **more_args: Unpack[DrawGridKwargs]) -> None:
        if clue_values is not None:
            d3 = self.clue_named('3d')
            special = int(clue_values[d3])
            sequences = len(SUM_LIST[d3.length][special])
            more_args['subtext'] = f'[{sequences}]'
        super().plot_board(clue_values, **more_args)


if __name__ == '__main__':
    Magpie223.run()
