import itertools
import pathlib
import pickle
from collections.abc import Hashable, Sequence
from math import sumprod
from typing import cast

from misc import divisor_count
from solver import DancingLinks, DLConstraint
from solver.dancing_links import get_row_column_optional_constraints
from solver.draw_grid import draw_grid

PUZZLE = "291--X--1..X--.1.-2..4..XX-8....7".replace("X", "---").replace("-", "...")
ROW_COUNT = [400, 96, 12, 315, 24, 12, 48, 24, 36]
COLUMN_COUNT = [9, 24, 24, 40, 672, 12, 24, 36, 12]


class Magpie218Solver:
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self):
        self.initial_grid = {
            (row, column): [int(letter)]
            for (row, column), letter in zip(
                itertools.product(range(1, 10), repeat=2), PUZZLE, strict=True)
            if '1' <= letter <= '9'}

    def solve(self):
        constraints: dict[Hashable, Sequence[DLConstraint]] = {
            ('SQUARE', row, column, value): [
                f"V{row}{column}", f"R{row}={value}",
                f"C{column}={value}", f"B{box}={value}",
                (f"r{row}c{column}", value)
            ]
            for row, column in itertools.product(range(1, 10), repeat=2)
            for box in [row - (row - 1) % 3 + (column - 1) // 3]
            for value in self.initial_grid.get((row, column), range(1, 10))}
        optional_constraints = get_row_column_optional_constraints(9, 9)
        table = self.generate_table()
        for rc_count in (ROW_COUNT, COLUMN_COUNT):
            is_row = rc_count is ROW_COUNT
            name = "ROW" if is_row else "COLUMN"
            for u, divisors in enumerate(rc_count, start=1):
                locations = [(f"r{u}c{i}" if is_row else f"r{i}c{u}")
                             for i in range(1, 10)]
                print(f"{name} {u} has {divisors} divisors: {len(table[divisors])}")
                for permutation in table[divisors]:
                    constraints[(name, u, permutation)] = [
                        f"Z-{name}-{u}",
                        *(zip(locations, permutation))
                    ]
        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=self.show_solution)
        solver.solve(debug=100)

    @staticmethod
    def generate_table() -> dict[int, Sequence[tuple[int, ...]]]:
        pickle_file = pathlib.Path("/tmp/primes.pcl")
        if pickle_file.exists():
            with pickle_file.open("rb") as file:
                return pickle.load(file)

        multiplier = [10 ** i for i in reversed(range(9))]
        result = {key: [] for key in {*ROW_COUNT, *COLUMN_COUNT}}
        for i, permutation in enumerate(itertools.permutations(range(1, 10))):
            if i % 10000 == 0:
                print(i)
            number = cast(int, sumprod(permutation, multiplier))
            count = divisor_count(number)
            if count in result:
                result[count].append(permutation)

        with pickle_file.open("wb") as file:
            pickle.dump(result, file)
        return result

    def show_solution(self, solution):
        solution = [x for x in solution if x[0] == 'SQUARE']
        grid = {(row, column): value for _, row, column, value in solution}
        draw_grid(max_row=10, max_column=10,
                  location_to_entry=grid,
                  top_bars=set(itertools.product((4, 7), range(1, 10))),
                  left_bars=set(itertools.product(range(1, 10), (4, 7))),
                  coloring=(dict.fromkeys(self.initial_grid, 'red')),
                  )


if __name__ == '__main__':
    Magpie218Solver().solve()
