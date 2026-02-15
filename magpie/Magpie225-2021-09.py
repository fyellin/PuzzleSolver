from __future__ import annotations

from collections.abc import Sequence
import math
from solver import Clue, ClueValue, Clues, ConstraintSolver, Constraint


def digit_sum(value: ClueValue | str | int) -> int:
    """
    Compute the sum of the decimal digits of the given value.
    
    Parameters:
        value (ClueValue | str | int): A value whose decimal digits will be summed; its string representation is iterated.
    
    Returns:
        int: Sum of the decimal digits in `value`.
    """
    return sum(int(x) for x in str(value))


GRID = """
XXX.X.X
..XX...
XX.X.X.
X.X.XXX
.X...X.
X..X...
"""

ACROSSES = [
    (1, 4),
    (4, 3),
    (6, 4),
    (8, 2),
    (10, 4),
    (12, 4),
    (15, 2),
    (17, 4),
    (19, 3),
    (20, 4),
]

DOWNS = [
    (1, 3),
    (2, 2),
    (3, 3),
    (4, 3),
    (5, 3),
    (7, 4),
    (9, 2),
    (11, 2),
    (12, 3),
    (13, 3),
    (14, 3),
    (16, 3),
    (18, 2),
]


class Magpie225 (ConstraintSolver):
    good_numbers: set[int]

    @staticmethod
    def run() -> None:
        solver = Magpie225()
        solver.solve(debug=True, max_debug_depth=200)
        solver.verify_is_180_symmetric()

    def __init__(self) -> None:
        clues = self.get_clues()
        constraints = self.get_constraints()
        super().__init__(clues, constraints=constraints)
        bad_numbers = {i + digit_sum(i) for i in range(1, 10_000)}
        self.good_numbers = set(range(1, 10_000)) - bad_numbers
        print(f"There are {len(self.good_numbers)} good numbers")

    def get_clues(self) -> Sequence[Clue]:
        def generator(_clue: Clue) -> set[int]:
            return self.good_numbers

        grid = Clues.get_locations_from_grid(GRID)
        return [
            Clue(f'{number}{"a" if is_across else "d"}', is_across, grid[number - 1], length, generator=generator)
            for information, is_across in ((ACROSSES, True), (DOWNS, False))
            for number, length in information
        ]

    @staticmethod
    def get_constraints() -> Sequence[Constraint]:
        def is_multiple(value1: ClueValue, value2: ClueValue) -> bool:
            return int(value1) % int(value2) == 0

        def is_square(value: ClueValue) -> bool:
            i_value = int(value)
            return math.isqrt(i_value) ** 2 == i_value

        return [
            Constraint(('4a', '2d'), is_multiple),
            Constraint(('10a', '19a'), is_multiple),
            Constraint(('17a', '9d'), is_multiple),
            Constraint(('1d', '18d'), is_multiple),
            Constraint(('3d', '15a'), is_multiple),
            Constraint(('14d', '2d'), is_multiple),
            Constraint(('16d', '8a'), is_multiple),
            Constraint(('15a',), is_square),
            Constraint(('12d',), is_square),
            Constraint(('13d',), is_square),
        ]


if __name__ == '__main__':
    Magpie225.run()