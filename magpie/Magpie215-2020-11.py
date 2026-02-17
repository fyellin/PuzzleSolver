import collections
import itertools
import math
from collections.abc import Sequence

from solver import Clue, Clues, ConstraintSolver, KnownClueDict, generators
from solver.generators import allvalues

GRID = """
XXXXXX
X.X...
XX.X..
X.XX.X
.X..X.
X..X..
"""


class Solver215(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver215()
        solver.verify_is_180_symmetric()
        solver.add_all_constraints()
        solver.solve(debug=True, max_debug_depth=50)
        solver.solve()

    def __init__(self) -> None:
        super().__init__(self.get_clue_list())

    def get_clue_list(self) -> Sequence[Clue]:
        grid_locations = [(-1, -1)] + Clues.get_locations_from_grid(GRID)

        across = ((1, 3, allvalues),
                  (5, 2, generators.palindrome),
                  (7, 2, allvalues),
                  (8, 3, generators.prime),
                  (9, 3, allvalues),
                  (11, 3, generators.palindrome),
                  (12, 3, generators.prime),
                  (14, 3, allvalues),
                  (16, 3, allvalues),
                  (17, 2, allvalues),
                  (18, 2, generators.square),
                  (19, 3, allvalues))
        down = ((1, 3, generators.prime),
                (2, 2, allvalues),
                (3, 3, allvalues),
                (4, 3, generators.palindrome),
                (5, 4, self.consecutive),
                (6, 3, allvalues),
                (10, 4, generators.cube),
                (12, 3, generators.square),
                (13, 3, generators.palindrome),
                (14, 3, self.consecutive),
                (15, 3, self.consecutive),
                (17, 2, generators.fibonacci))
        clues = [
            Clue(f'{number}{suffix}', is_across, grid_locations[number], length, generator=generator)
            for clue_list, is_across, suffix in ((across, True, 'a'), (down, False, 'd'))
            for number, length, generator in clue_list
        ]
        return clues

    def add_all_constraints(self) -> None:
        self.add_constraint(('7a', '11a'), self.is_factor)
        self.add_constraint(('5a', '9a'), self.is_factor)
        self.add_constraint(('14a', '19a'), lambda a14, a19: self.is_palindrome(int(a19) - int(a14)))
        self.add_constraint(('16a', '3d'), self.is_factor)
        self.add_constraint(('17a', '7a', '18a'), lambda a17, a7, a18: int(a17) == int(a7) + int(a18))
        self.add_constraint(('2d', '9a'), self.is_factor)
        self.add_constraint(('16a', '3d'), self.is_factor)
        self.add_constraint(('6d', '15d'), lambda d6, d15: self.is_square(int(d15) - int(d6)))
        clue1 = self.clue_named("1a")
        others = [clue for clue in self._clue_list if clue.length == clue1.length and clue != clue1]
        others.insert(0, clue1)
        self.add_constraint(others, lambda *args: self.first_is_jumble(args))

    def consecutive(self, clue: Clue) -> Sequence[str]:
        length = clue.length
        for start in range(1, 11 - length):
            result = ''.join(str(start + i) for i in range(length))
            yield result
            yield result[::-1]

    @staticmethod
    def is_factor(value1: str, value2: str):
        return int(value2) % int(value1) == 0

    @staticmethod
    def is_square(value):
        return value > 0 and math.isqrt(value) ** 2 == value

    @staticmethod
    def is_palindrome(value):
        return value > 0 and (temp := str(value)) == temp[::-1]

    @staticmethod
    def first_is_jumble(args):
        first, *others = args
        ffirst = tuple(first)
        for other in others:
            for permutation in itertools.permutations(other):
                if ffirst == permutation:
                    return True
        return False

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        location_to_value = {location : char
                             for clue, value in known_clues.items()
                             for location, char in zip(clue.locations, value)}
        counter = collections.Counter(location_to_value.values())
        if '0' in counter:
            return False
        for i in range(1, 10):
            temp = counter[str(i)]
            if temp > 0 and temp != i:
                return False
        return True

if __name__ == '__main__':
    Solver215.run()
