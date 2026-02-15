from __future__ import annotations

import itertools
from collections.abc import Iterable
from typing import Any, Optional, Sequence, cast

from misc.primes import PRIMES
from solver import ClueValue, Clues, EquationSolver, Evaluator, KnownClueDict, KnownLetterDict


class MultiValue:
    values: set[int]
    __name: Optional[str]

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
2 FF (4)
5 A (2) 
6 G (2) 
8 D (2) 
10 A (2)
12 H (2)
13 J – D (3)
14 A – F (2)
15 B (2)
16 D (2)
18 F (2)
20 B (2)
21 AC (4)"""

DOWNS = """
1 G (2) 
3 C (2) 
4 (G + D)(G – D) – E (3) 
5 AA (4) 
7 BB (4) 
9 DD (3) 
11 F –B (2) 
12 E (2) 
13 J (3) 
17 C (2) 
19 F (2)
"""

GRID = """
XXX.XX.
XXXXX.X
X.X..X.
.X.XXXX
X.X....
"""


class Magpie234 (EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie234()
        solver.verify_is_180_symmetric()
        # solver.plot_board()
        solver.solve(debug=False, max_debug_depth=2)

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
        super().__init__(clues, items=cast(tuple[int], self.get_non_primes()))

    def check_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> bool:
        temp = {location: int(value)
                for clue, value in known_clues.items()
                for location, value in zip(clue.locations, value)}
        assert len(temp) == 35
        return sum(temp.values()) in known_letters['J']

    def draw_grid(self, **args: Any) -> None:
        super().draw_grid(font_multiplier=.8, **args)

    @staticmethod
    def get_non_primes():
        results = []
        for x in range(10, 1000):
            if x not in PRIMES:
                rev_x = int(str(x)[::-1])
                if x < rev_x and rev_x not in PRIMES:
                    results.append(MultiValue({x, rev_x}))
        return results

if __name__ == '__main__':
    Magpie234.run()
