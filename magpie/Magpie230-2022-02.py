from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Any, cast

from solver import ClueValue, Clues, EquationSolver, Evaluator


class MultiValue:
    values: set[int]
    __name: str | None

    @staticmethod
    def make(a, b):
        assert 1 <= a < b <= 9
        result = MultiValue({10 * a + b, 10 * b + a})
        return result

    @classmethod
    def make_all(cls):
        return tuple(cls.make(a, b) for a, b in itertools.combinations(range(1, 10), 2))

    def __init__(self, values: set[int]):
        self.values = values
        self.__name = None

    def __add__(self, other: MultiValue) -> MultiValue:
        result = {a + b for a in self.values for b in other.values}
        return MultiValue(result)

    def __mul__(self, other: MultiValue) -> MultiValue:
        result = {a * b for a in self.values for b in other.values}
        return MultiValue(result)

    def __sub__(self, other: MultiValue) -> MultiValue:
        result = {a - b for a in self.values for b in other.values if a > b}
        return MultiValue(result)

    def __contains__(self, item: int) -> bool:
        return item in self.values

    def __str__(self):
        if not self.__name:
            self.__name = '/'.join(str(x) for x in sorted(self.values))
        return self.__name

    def __repr__(self):
        return str(self)

    # These two are quick hacks so that show_letter_values() will work.
    # Efficiency (especially of __lt__) just doesn't matter

    def __format__(self, format_spec: str) -> str:
        return str(self).__format__(format_spec)

    def __lt__(self, other):
        return min(self.values) < min(other.values)


ACROSSES = """
1 MMS (6)
6 PY (4)
9 AAN (5)
10 AS(B - A) (5)
11 AHR (5)
13 PY (4)
15 DII (6)
19 NT(P - A) (4)
20 BHS (5)
22 HSY (5)
24 TTY (5)
25 NS (4)
26 YYY (6)
"""

DOWNS = """
1 O(B-B) (4)
2 CNR (5)
3 OW (4)
4 EL (3)
5 LPW (5)
6 YY (4)
7 A (2)
8 ET (3)
12 STY (5)
14 DTY (5)
16 RS (4)
17 TY (4)
18 YYY (4)
19 EN (3)
21 N+S (3)
23 E (2)
"""

GRID = """
XXXX.XXX.X
X....X....
X...X.X.X.
..XX...X.X
X....XX...
X.X..X....
X...X.....
"""


class Magpie230 (EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie230()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True, max_debug_depth=10)

    def __init__(self) -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSSES, DOWNS, grid)

        def my_wrapper(evaluator: Evaluator, value_dict: dict) -> Iterable[ClueValue]:
            try:
                # All of our arguments should be MultiValue.  Hence the result of what looks like a simple
                # calculation will also be a MultiValue.  So we just need to convert the MultiValue to a list
                # of values.  No filtering is necessary since we toss out all negative numbers in the - operator.
                result = evaluator.raw_call(value_dict)
                return (ClueValue(str(x)) for x in cast(MultiValue, result).values)
            except ArithmeticError:
                return ()

        for clue in clues:
            for evaluator in clue.evaluators:
                evaluator.set_wrapper(my_wrapper)

        # This cast is a bald-faced lie.  But it works.
        super().__init__(clues, items=cast(tuple[int], MultiValue.make_all()))

    def draw_grid(self, **args: Any) -> None:
        super().draw_grid(font_multiplier=.8, **args)


if __name__ == '__main__':
    Magpie230.run()
