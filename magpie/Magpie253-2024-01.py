import itertools
import math
from typing import Any, Optional

from networkx import Graph, greedy_color

from misc.Pentomino import PentominoSolver, get_graph_shading
from solver import Clue, ClueValue, Clues, ConstraintSolver, Location
from solver.constraint_solver import LetterCountHandler
from solver.equation_solver import KnownClueDict
from solver.generators import allvalues, fibonacci, known, palindrome, prime, \
    triangular


def dp(x):
    return math.prod(int(i) for i in str(x))


def ds(x):
    return sum(int(i) for i in str(x))


def is_cube(x):
    return round(x ** (1 / 3)) ** 3 == x


def is_square(x):
    return math.isqrt(x) ** 2 == x


def is_prime(x):
    return all(x % i for i in range(2, math.isqrt(x) + 1))


def is_harshad(x):
    return x % ds(x) == 0


GRID = """
XX.XXX.X
..X..X..
X..X..X.
XX.XX.X.
X.X..X.X
...X..X.
X.XXX...
X...X...
"""

ACROSSES = ((1, 4), (4, 4), (7, 3), (8, 3), (9, 2), (10, 2), (12, 3), (14, 3),
            (16, 2), (17, 2), (18, 3), (19, 3), (21, 2), (22, 2), (23, 3), (25, 3),
            (27, 4), (28, 4))

DOWNS = ((1, 4), (2, 3), (3, 2), (4, 3), (5, 2), (6, 4), (10, 3), (11, 3),
         (13, 3), (15, 3), (17, 4), (20, 4), (21, 3), (22, 3), (24, 2), (26, 2))


class Magpie253 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie253()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, letter_handler=self.MyLetterHandler())
        self.__get_constraints()
        self.coloring = None

    def get_clues(self):
        clues = []
        grid = Clues.get_locations_from_grid(GRID)
        for (index, length) in ACROSSES:
            clues.append(Clue(f'{index}a', True, grid[index - 1], length))
        for (index, length) in DOWNS:
            clues.append(Clue(f'{index}d', False, grid[index - 1], length))
        for clue in clues:
            clue.generator = allvalues
        return clues

    def draw_grid(self, location_to_entry, **more_args: Any) -> None:
        shading = {}
        if location_to_entry:
            # Figure out how to divide the graph into pentominos

            one_of_each = {"1", "2", "3", "4", "5"}

            def predicate(squares):
                return {location_to_entry.get(square) for square in squares} == one_of_each

            solutions = PentominoSolver().solve(8, 8, predicate)
            if solutions:
                solution, = solutions
                shading = get_graph_shading(solution)
        super().draw_grid(location_to_entry=location_to_entry,
                          shading=shading, **more_args)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        value = dp(known_clues[self.clue_named('17d')])
        counter = self._letter_handler._counter
        expected_value = sum(int(key) for key, value in counter.items() if value) * 12
        return value == expected_value

    class MyLetterHandler(LetterCountHandler):
        def real_checking_value(self, value: ClueValue, _info: Any) -> bool:
            counter = self._counter
            return sum(x > 0 for x in counter.values()) <= 5 and max(counter.values()) <= 12

    def __get_constraints(self):
        self.add_constraint("4a 26d", lambda x, y: ds(x) == int(y))
        self.clue_named("7a").generator = known(*{y * (y + 1) for y in range(50)})
        self.clue_named("8a").generator = known(*{5 * y * y for y in range(50)})
        self.add_constraint("9a 17a", lambda x, y: x == y[::-1])
        self.clue_named("10a").generator = known(*{y * y - y for y in range(50)})
        self.add_constraint("12a", lambda x: x[0] < x[1] < x[2])
        self.add_constraint("14a", lambda x: dp(x) == 5 * ds(x))
        self.clue_named("16a").generator = triangular
        self.clue_named("17a").generator = fibonacci
        self.add_constraint("18a", lambda x: is_harshad(int(x)) and is_cube(int(x) + 1))
        self.add_constraint("19a", lambda x: x[0] > x[1] > x[2])
        self.add_constraint("21a", lambda x: dp(x) > 0 and int(x) % dp(x) == 0 and int(x) % ds(x) == 0
                                             and (ds(x) * dp(x)) % int(x) == 0)
        self.clue_named("22a").generator = triangular
        self.clue_named("23a").generator = known(1, 5, 12, 22, 35, 51, 70, 92, 117, 145, 176, 210, 247, 287, 330, 376, 425, 477, 532, 590, 651, 715, 782, 852, 925)
        self.clue_named("25a").generator = known(*{x**2 + y**2
                                                   for x in range(40) for y in range(40)})
        self.clue_named("27a").generator = known(1024, 1296, 2048, 3125, 4096, 7776, 8192)
        self.add_constraint("28a 27a", lambda x, y: dp(x) == 2 * dp(y))

        self.add_constraint("1d", lambda x: is_square(dp(x)) and is_square(ds(x)))
        self.add_constraint("2d 10a 18a", lambda x, y, z: int(x) == int(y) + int(z))
        self.add_constraint("2d 16a 19a", lambda x, y, z: int(x) == int(y) + int(z))
        self.clue_named("3d").generator = palindrome
        self.clue_named("4d").generator = known(*{str(y * y)[::-1] for y in range(40)})
        self.clue_named("5d").generator = palindrome
        self.clue_named("6d").generator = prime
        self.add_constraint("6d 1a", lambda x, y: sorted(x) == sorted(y))
        self.clue_named("10d").generator = prime
        self.add_constraint("11d", lambda x: is_harshad(int(x)))
        self.clue_named("13d").generator = known(176, 225, 280, 341, 408, 481, 560, 645,
                                                 736, 833, 936)
        self.add_constraint("15d", lambda x: dp(x) == 2 * ds(x))
        # We don't have an easy way of integrating this with MyLetterHandler.  Once we
        # know the five digits, the dp(x) has to be 12 times the sum. But it does have to
        # be a multiple of 12, and 0+1+2+3+4=10, 5+6+7+8+9=35.
        self.add_constraint("17d", lambda x: dp(x) % 12 == 0 and 10 <= dp(x) // 12 <= 35)
        self.add_constraint("20d", lambda x: is_square(dp(x)))
        self.add_constraint("21d 19a", lambda x, y: x == y[::-1])
        self.clue_named("22d").generator = known(*{y**3 + z**3
                                                   for y in range(10) for z in range(10)})
        self.clue_named("24d").generator = known(*{str(y * y)[::-1] for y in range(50)})
        self.clue_named("26d").generator = known(14, 30, 55, 91,)


if __name__ == '__main__':
    Magpie253.run()
