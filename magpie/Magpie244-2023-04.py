import collections
import itertools
import math
from functools import cache
from typing import NamedTuple

from solver import Clues, ConstraintSolver, DancingLinks
from solver.dancing_links import get_row_column_optional_constraints

ACROSSES = "34/421/34/151/43/124/43"
DOWNS = "43/124/43/151/34/421/34"


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
        return {(r, c) for r, c in items if 1 <= r <= 7 and 1 <= c <= 7}

    def get_self_and_penumbra(key) -> set[tuple[int, int]]:
        items = {(r + dr, c + dc)
                 for r, c in key.get_squares()
                 for dr in (-1, 0) for dc in (-1, 0)
                 }
        return {(r, c) for r, c in items if 1 <= r <= 7 and 1 <= c <= 7}


class Magpie244(ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie244()
        solver.verify_is_four_fold_symmetric()
        solver.solve()

    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSSES, DOWNS)
        super().__init__(clues)

        self.locations = set(itertools.product(range(1, 8), repeat=2))
        self.start_locations = list(filter(self.is_start_location, self.locations))
        self.squares = {str(x * x) for x in range(10, 32)} - {'729'}

    def find_answers(self, items=None):
        items = items or [101, 7771, 5101, 21, 110, 1910, 82999, 1811, 910, 81,
                          1200, 1826, 610, 1511, 1002, 729, 7119, 100, 11, 8888,
                          9926, 1000, 111, 112, 10]

        def my_map(number: int) -> str:
            if number == 2:
                return 'd'
            if number == 3:
                return 'e'
            if number == 5:
                return 'h'
            if number == 10:
                return 'o'
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

    def solve(self, debug=None):
        constraints = {}
        optional_constraints = get_row_column_optional_constraints(7, 7)

        for key in RowName.get_all_keys():
            constraints[key] = [f'L-{key.length}',
                                *(f'r{r}c{c}' for r, c in key.get_self_and_penumbra())]
        dl = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=self.verify_solution)
        dl.solve()

    def verify_solution(self, solution: list[RowName]):
        counts = collections.Counter(x for key in solution for x in key.get_shadow())
        for key in solution:
            for square in key.get_squares():
                counts[square] = key.length + 4
        if any(counts[square] == 0 for square in self.start_locations):
            return
        locations = {(row, column): str(counts[row, column])
                     for row in range(1, 8) for column in range(1, 8)}

        entry = tuple(''.join(locations[x] for x in clue.locations) for clue in self.clue_list)
        entry_set = set(entry)
        if len(entry_set) != len(entry):
            return
        if '81' not in entry_set or '729' not in entry_set:
            return
        if self.squares.isdisjoint(entry_set):
            return
        known_clues = dict(zip(self.clue_list, entry, strict=True))

        shading = {location: (.8, 1.0, .8)
                   for location, value in locations.items()
                   if value >= '5'}

        print(known_clues)
        self.plot_board(known_clues, location_to_clue_numbers={}, shading=shading)


if __name__ == '__main__':
    Magpie244.run()
