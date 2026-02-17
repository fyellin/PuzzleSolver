from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence
from functools import cache
from typing import Any

from misc import PRIMES
from solver import Clues, ClueValue, EquationSolver, Evaluator, KnownClueDict,  \
    KnownLetterDict

ACROSS_LENGTHS = "413/332/44/44/233/314"
DOWN_LENGTHS = "222/33/24/33/33/42/33/222"

ACROSSES = """
1 VY
6 AHPY
9 P*T
10 MPX
11 R
12 FPY
14 NPTY
16 DY
19 MSW
21 E
22 HMP*Y
23 OP*
25 AS
26 LMP*Y
"""

DOWNS = """
1 HY*
2 K
3 PY*
4 APX
5 CM
6 GMP
7 BMP
8 T
12 M*Y
13 HLU
15 IM
17 HMPY
18 MP*Y
19 HP*Y*
20 PWY
21 HPY
23 MP
24 MP*Y
"""

class MultiValue:
    values: list[int]

    @staticmethod
    @cache
    def power(value,  maximum=10_000):
        values = []
        next = value * value
        while next < maximum:
            values.append(next)
            next *= value
        if not values:
            return MultiValue.NONE
        elif len(values) == 1:
            return values[0]
        return MultiValue(values, maximum)

    def __init__(self, values: Sequence[int], maximum: int = 10_000) -> None:
        self.values = values
        self.maximum = maximum

    def __mul__(self, other) -> MultiValue:
        maximum = self.maximum
        if isinstance(other, int):
            values = [t for x in self.values if (t := x * other) < maximum]
        elif isinstance(other, MultiValue):
            values = [t for x, y in itertools.product(self.values, other.values) if (t := x * y) < maximum]
        if not values:
            return MultiValue.NONE
        elif len(values) == 1:
            return values[0]
        return MultiValue(values)

    __rmul__ = __mul__

    @staticmethod
    def wrapper(self, value_dict: KnownLetterDict) -> Iterable[ClueValue]:
        try:
            result = self._compiled_code(*(value_dict[x] for x in self._vars))
            if isinstance(result, int):
                return ClueValue(str(result)),
            elif isinstance(result, MultiValue):
                return [ClueValue(str(v)) for v in result.values]
        except ArithmeticError:
            pass
        return ()

class NoneValue:
    def __mul__(self, other) -> MultiValue:
        return self

    __rmul__ = __mul__


MultiValue.NONE = NoneValue()


class Magpie274 (EquationSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        # solver.plot_board()
        solver.solve(debug=True, max_debug_depth=0)
        # solver.verify_is_180_symmetric()
        # solver.solve()

    def __init__(self) -> None:
        clues = self.get_clues()
        primes = [x for x in PRIMES if x < 2500]
        super().__init__(clues, items=primes)
        self.clue_named("9a").priority = 20  # solve first
        self.clue_named("3d").priority = 10

    def get_clues(self):
        acrosses = ACROSSES.replace('*', '!')
        downs = DOWNS.replace('*', '!')
        clues = Clues.create_from_text2(acrosses, downs, ACROSS_LENGTHS, DOWN_LENGTHS)
        for clue in clues:
            if '!' in clue.expression:
                clue.evaluators = Evaluator.create_evaluators(
                    clue.expression,
                    mapping={'fact': MultiValue.power},
                    wrapper=MultiValue.wrapper)
        return clues

    def check_solution(self, known_clues: KnownClueDict, _known_letters: KnownLetterDict) -> bool:
        grid = {location: int(char) for clue, value in known_clues.items()
                for location, char in zip(clue.locations, value)}
        self.line = doit(grid)
        return bool(self.line)

    def draw_grid(self, **args: Any) -> None:
        import numpy as np
        points = np.array(self.line)
        def extra(_plt, axes):
            axes.plot(points[:,1] + .5, points[:,0] + .5)
        super().draw_grid(subtext="COLLATZ", extra=extra,  **args)


def doit(board):
    all_locations = set(board.keys())

    def attempt(path, unseen, current_value, used=0) -> Iterable[list[tuple[int, int]]]:
        string = str(current_value)
        if used == len(string):
            if not unseen:
                yield path
            else:
                yield from attempt(path, unseen, current_value * 2)
                if current_value % 6 == 4 and current_value > 6:
                    yield from attempt(path, unseen, current_value // 3)
        else:
            digit = int(string[~used])
            row, column = path[0]
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                temp = (row + dr, column + dc)
                if temp in unseen and board[temp] in (digit, -1):
                    yield from attempt([temp, *path], unseen - {temp}, current_value, used + 1)

    def start_path():
        for location, value in board.items():
            if value == 1 or value == -1:
                yield from attempt([location], all_locations - {location}, 2)

    result = list(start_path())
    assert len(result) <= 1
    return result[0] if result else None


if __name__ == '__main__':
    Magpie274.run()
