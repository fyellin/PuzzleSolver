import math
from typing import Any

from misc.Pentomino import get_graph_shading, get_hard_bars
from solver import Clue, ClueValue, Clues, ConstraintSolver, DancingLinks, Location
from solver.constraint_solver import LetterCountHandler
from solver.generators import allvalues, cube, known, palindrome, prime, \
    square, sum_of_2_cubes, triangular


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


GRID = """
X.XXXXXX
XX.X.X..
X..X.X.X
.X..XX..
X.XX.XX.
X..X.X.X
X.X..X..
"""

ACROSSES = ((1, 3), (3, 3), (6, 2), (8, 3), (10, 2), (11, 3), (12, 3), (13, 2), (14, 3),
            (16, 3), (17, 3), (19, 3), (21, 2), (22, 3), (24, 3), (25, 2), (26, 3),
            (28, 2), (29, 3), (30, 3))

DOWNS = ((1, 2), (12, 3), (24, 2), (9, 2), (16, 4), (2, 4), (20, 3), (3, 4), (21, 3),
         (4, 3),  (17, 4), (5, 3), (18, 4), (6, 4), (23, 2), (7, 2), (15, 3), (27, 2))


class Magpie253 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie253()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, letter_handler=self.MyLetterHandler())
        self.__get_constraints()
        # self.coloring = None

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

    def get_allowed_regexp(self, location: Location) -> str:
        return '[1-6]' if self.is_start_location(location) else '[0-6]'

    class MyLetterHandler(LetterCountHandler):
        def real_checking_value(self, value: ClueValue, _info: Any) -> bool:
            counter = self._counter
            return all(x <= 8 for x in counter.values())

    def draw_grid(self, location_to_entry, location_to_clue_numbers,
                  top_bars, left_bars, max_row, max_column, **args: Any) -> None:
        constraints = {}
        for row in range(1, max_row):
            for column in range(1, max_column):
                if column != max_column - 1:
                    pair = location_to_entry[row, column], location_to_entry[row, column + 1]
                    constraints[(row, column), (row, column + 1)] = [
                        f"R{row}C{column}", f"R{row}C{column + 1}", min(pair)+max(pair)]
                if row != max_row - 1:
                    pair = location_to_entry[row, column], location_to_entry[row + 1, column]
                    constraints[(row, column), (row + 1, column)] = [
                        f"R{row}C{column}", f"R{row + 1}C{column}", min(pair)+max(pair)]
        solutions = []
        solver = DancingLinks(constraints, row_printer=lambda x: solutions.append(x))
        solver.solve(debug=True)
        solution, = solutions
        shading = get_graph_shading(solution)
        left_bars2, top_bars2 = get_hard_bars(solution)
        super().draw_grid(location_to_entry=location_to_entry,
                          max_row=max_row, max_column=max_column,
                          top_bars=top_bars2, left_bars=left_bars2,
                          shading=shading, **args)
        super().draw_grid(location_to_entry=location_to_entry,
                          max_row=max_row, max_column=max_column,
                          location_to_clue_numbers=location_to_clue_numbers,
                          top_bars=top_bars, left_bars=left_bars, **args)

    def __get_constraints(self):
        def is_factor(x, y): return int(y) % int(x) == 0
        def is_multiple(x, y): return int(x) % int(y) == 0

        self.clue_named("1a").generator = triangular
        self.clue_named("3a").generator = prime
        self.add_constraint("6a 25a", lambda x, y: x == y[::-1])
        self.add_constraint("8a 5d 29a", lambda x, y, z: int(x) == int(y) - int(z))
        self.add_constraint("10a 17a", is_factor)
        self.clue_named("11a").generator = triangular
        self.clue_named("12a").generator = prime
        self.clue_named("13a").generator = prime
        self.add_constraint("13a", lambda x: is_prime(int(x[::-1])))
        # add that 13a is also a reverse prime
        self.clue_named("14a").generator = prime
        self.add_constraint("16a 11a 1d", lambda x, y, z: int(x) == int(y) + int(z))
        self.clue_named("17a").generator = sum_of_2_cubes
        self.add_constraint("19a 6a", is_multiple)
        self.clue_named("21a").generator = known(18, 32, 50, 72, 98)
        self.add_constraint("22a 21a", lambda x, y: dp(x) == int(y))
        self.clue_named("25a").generator = prime
        self.add_constraint("26a 13a", is_multiple)
        self.clue_named("28a").generator = triangular
        self.add_constraint("29a 23d", is_multiple)
        self.clue_named("30a").generator = palindrome

        self.add_constraint("1d 28a 7d", lambda x, y, z: int(x) == int(y) - int(z))
        self.add_constraint("2d 21d 13a", lambda x, y, z: int(x) % (int(y) + int(z)) == 0)
        self.add_constraint("3d 2d 23d 22a", lambda x, y, z, w: int(x) == int(y) + int(z) - int(w))
        self.clue_named("4d").generator = prime
        self.add_constraint("4d", lambda x: x == x[::-1])
        self.add_constraint("5d 24a 24d", lambda x, y, z: int(x) == int(y) + int(z))
        self.clue_named("6d").generator = triangular
        self.clue_named("7d").generator = square
        self.clue_named("9d").generator = triangular
        self.clue_named("12d").generator = cube
        self.add_constraint("15d 25a", is_multiple)
        self.add_constraint("16d 1d 6d 12d", lambda x, y, z, w:  int(x) == int(y) + int(z) + int(w))
        self.add_constraint("17d 4d 20d 9d", lambda x, y, z, w: int(x) == (int(y) + int(z)) * int(w))
        self.add_constraint("18d 1d 27d", lambda x, y, z: int(x) == int(y) * int(z))
        self.add_constraint("20d 28a 5d", lambda x, y, z: int(x) == int(y) + int(z))
        self.add_constraint("21d", lambda x: is_square(int(x[::-1])))
        self.clue_named("23d").generator = known(21, 55)
        self.clue_named("24d").generator = square
        self.add_constraint("24d 6d", is_factor)
        self.add_constraint("27d 13a 25a", lambda x, y, z: int(x) == int(y) + int(z))



if __name__ == '__main__':
    Magpie253.run()
