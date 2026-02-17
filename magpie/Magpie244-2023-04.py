import collections
import itertools
import math
import pickle
from functools import cache
from pathlib import Path
from typing import Any, NamedTuple

from solver import Clue, Clues, ConstraintSolver, DancingLinks

GRID = """
X.XXXXX
XX..X..
X..X....
.X..X.X
X.X.XX.
.X.X...
X...X..
"""

ACROSSES = [
    (1, 3), (3, 4), (7, 4), (9, 2), (10, 3), (11, 4), (12, 5),
    (15, 4), (17, 3), (19, 2), (20, 4), (21, 4), (22, 3)
]
DOWNS = [
    (1, 4), (2, 4), (4, 3), (5, 4), (6, 3), (8, 2), (12, 4), (13, 4), (14, 4),
    (15, 3), (16, 3), (18, 2)
]


class RowName (NamedTuple):
    row: int
    column: int
    length: int
    is_across: bool

    @staticmethod
    def get_all_keys() -> set[RowName]:
        squares = list(itertools.product(range(1, 8), repeat=2))
        result = set()
        for r, c in squares:
            for length in (1, 2, 3, 4):
                if c + length <= 8:
                    result.add(RowName(r, c, length, True))
                if r + length <= 8 and length > 1:
                    result.add(RowName(r, c, length, False))
                if 2 <= r <= 6 and 2 <= c <= 6:
                    result.add(RowName(r, c, 5, True))
        return result

    @cache
    def get_squares(self) -> set[tuple[int, int]]:
        r, c, length = self.row, self.column, self.length
        if length == 5:
            result = {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}
        elif self.is_across:
            result = {(r, c + i) for i in range(length)}
        else:
            result = {(r + i, c) for i in range(length)}
        assert all(1 <= row <= 7 and 1 <= column <= 7 for row, column in result)
        assert len(result) == length
        assert (r, c) in result
        return result

    @cache
    def get_shadow(self) -> set[tuple[int, int]]:
        items = {(r + dr, c + dc)
                 for r, c in self.get_squares()
                 for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                 }
        items -= self.get_squares()
        items -= self.get_squares()
        return {(r, c) for r, c in items if 1 <= r <= 7 and 1 <= c <= 7}

    def __lt__(self, other):
        return (-self.length, self.row, self.column, self.is_across) < \
            (-other.length, other.row, other.column, other.is_across)

    def __repr__(self):
        return f"<{self.length}@{self.row}{self.column} {'A' if self.is_across else 'D'}>"

    def flip_x(self) -> RowName:
        row, column, length, is_across = self
        if length == 5 or not is_across:
            return RowName(row, 8 - column, length, is_across)
        else:
            return RowName(row, 8 - column - (length - 1), length, True)

    def flip_y(self) -> RowName:
        row, column, length, is_across = self
        if length == 5 or is_across:
            return RowName(8 - row, column, length, is_across)
        else:
            return RowName(8 - row - (length - 1), column, length, is_across)

    def rotate(self) -> RowName:
        row, column, length, is_across = self
        if not is_across:
            row += length - 1
        row2, column2 = column, 8 - row
        is_across2 = length == 1 or length == 5 or not is_across
        return RowName(row2, column2, length, is_across2)


class Magpie244(ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie244()
        # solver.plot_board({})
        solver.verify_is_180_symmetric()
        solver.doit()
        solver.find_answers()

    def __init__(self):
        locations = Clues.get_locations_from_grid(GRID)
        clues = self.get_clues(locations)
        self.square_set = set(itertools.product(range(1, 8), repeat=2))
        super().__init__(clues)

    def doit(self):
        path = Path('/tmp/entries_list')
        if path.exists():
            with open(path, "rb") as file:
                entries_list = pickle.load(file)
            print(f'Read {len(entries_list)} entry lists')
        else:
            solutions = self.get_solutions()
            print(f'Generated {len(solutions)} solutions')
            entries_list = [self.solution_to_entries(solution) for solution in solutions]
            with open(path, 'wb') as file:
                pickle.dump(entries_list, file)
            print(f'Wrote {len(entries_list)} entry lists')

        print(len(entries_list))
        square_roots = {str(x * x) for x in range(10, 32)} - {'729'}
        entries_list = [entries for entries in entries_list
                        if len(entries) == len(set(entries))
                        if all(entry[0] != '0' for entry in entries)
                        if '81' in entries and '729' in entries
                        if not square_roots.isdisjoint(entries)
                        ]
        print(len(entries_list))

        for entries in entries_list:
            clue_values = dict(zip(self._clue_list, entries))
            self.plot_board(clue_values)
            print([int(x) for x in entries])

    def find_answers(self, items=None):
        items = items or [101, 7771, 5101, 21, 110, 1910, 82999, 1811, 910, 81,
                          1200, 1826, 610, 1511, 1002, 729, 7119, 100, 11, 8888,
                          9926, 1000, 111, 112, 10]

        def my_map(number: int) -> str:
            if number == 2: return 'd'
            if number == 3: return 'e'
            if number == 5: return 'h'
            if number == 10: return 'o'
            return 'r'

        d, e, h, o = 2, 3, 5, 10
        for r in (4, 6, 8, 12, 16, 20, 24):
            products = collections.defaultdict(list)
            for numbers in itertools.combinations_with_replacement((d, e, h, o, r), 4):
                product = math.prod(numbers)
                if product in (1000, 1200):
                    code = ''.join(my_map(x) for x in numbers)
                    products[product].append(code)
            print(r, products[1000], products[1200])

    def solution_to_entries(self, solution):
        counts = collections.Counter(x for key in solution for x in key.get_shadow())
        locations = {(row, column): str(counts[row, column])
                     for row in range(1, 8) for column in range(1, 8)}
        for key in solution:
            for square in key.get_squares():
                assert locations[square] == '0'
                locations[square] = str(key.length + 4)
        entries = tuple(''.join(locations[x] for x in clue.locations)
                        for clue in self._clue_list)
        return entries

    def draw_grid(self, location_to_entry, **args: Any) -> None:
        shading = {location: (.8, 1.0, .8)
                   for location, value in location_to_entry.items()
                   if value >= '5'}
        # for ch, location in zip('HOOD', self.clue_named('14d').locations):
        #     location_to_entry[location] = ch
        # for ch, location in zip('HERO', self.clue_named('20a').locations):
        #     location_to_entry[location] = ch
        args |= {"shading": shading, "location_to_clue_numbers": {}}
        super().draw_grid(location_to_entry=location_to_entry, **args)

    def get_solutions(self, debug=None):
        path = Path('/tmp/solutions')
        if path.exists():
            with open(path, 'rb') as file:
                solutions = pickle.load(file)
                print(f'Read file with {len(solutions)} solutions')
                return solutions
        square_set = set(itertools.product(range(1, 8), repeat=2))
        constraints = {}
        optional_constraints = {f'r{r}c{c}' for r, c in square_set}

        def get_shadow(key) -> set[tuple[int, int]]:
            items = {(r + dr, c + dc)
                     for r, c in key.get_squares()
                     for dr in (-1, 0) for dc in (-1, 0)
                     # for dc, dr in ((-1, -1), (0, -1), (1, -1), (0, 0))
                     }
            return {(r, c) for r, c in items if 1 <= r <= 7 and 1 <= c <= 7}

        for key in RowName.get_all_keys():
            constraints[key] = [f'L-{key.length}']
            constraints[key].extend(f'r{r}c{c}' for r, c in get_shadow(key))

        solutions = []

        dl = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=lambda x: solutions.append(x))
        dl.solve(debug=debug)
        print('End', len(solutions))
        solutions = [tuple(sorted(x)) for x in solutions]
        solutions.sort()
        with open(path, 'wb') as file:
            pickle.dump(solutions, file)
            print(f'Write file with {len(solutions)} solutions')
        return solutions

    def get_clues(self, locations):
        clues = []
        for lines, is_across, letter in ((ACROSSES, True, 'a'), (DOWNS, False, 'd')):
            for number, length in lines:
                clue = Clue(f'{number}{letter}', is_across, locations[number - 1], length)
                clues.append(clue)
        return clues


if __name__ == '__main__':
    Magpie244.run()
