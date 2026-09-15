import itertools
from collections.abc import Sequence

import more_itertools
from more_itertools import is_prime
from rich import print as pprint
from rich.markup import escape

from solver import (
    BaseSolver,
    Clue,
    DancingLinks,
)

CLUES = [
    *[Clue(str(number), True, (r, c), 3)
      for (number, r, c) in [(1, 1, 4), (5, 2, 1), (9, 6, 4), (14, 8, 1), (15, 8, 7), (16, 9, 1)]],
    *[Clue(str(number), False, (r, c), 3)
      for (number, r, c) in [(2, 1, 6), (3, 1, 8), (4, 1, 9), (6, 4, 1), (7, 4, 3), (8, 4, 6),
                             (10, 7, 1), (11, 7, 2), (12, 7, 5), (13, 7, 9),]]
]


class Listener4934(BaseSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True, max_debug_depth=4)

    def __init__(self):
        super().__init__(CLUES)
        self.constraints = {}
        self.optional_constraints = set()
        self.get_constraints()
        self.dancing_links = DancingLinks(constraints=self.constraints,
                                          optional_constraints=self.optional_constraints,
                                          row_printer=self.on_solve)

    def solve(self, *, show_time: bool = True, debug: bool = False,
              max_debug_depth: int | None = None) -> int:
        self.dancing_links.solve(debug=debug, max_debug_depth=max_debug_depth)
        return 0

    def get_constraints(self):
        constraints = self.constraints

        self.optional_constraints.update(
            x for i, j in itertools.product(range(1, 10), repeat=2)
            for x in (f'xr{i}c{j}', f'xr{i}v{j}', f'xc{i}v{j}')
        )

        for value in more_itertools.sieve(1000):
            if value >= 100 and '0' not in (s := str(value)) and len(set(s)) == 3:
                self.set_value((4, value))
                self.set_value((12, value))
                if value < 500 and '0' not in (s2 := str(value * 2)) and len(set(s2)) == 3:
                    if s[1] not in s2:
                        # Middle digit of 5a can't be in 11d
                        self.set_value((5, value), (11, 2 * value))

                    if not any(s2[i] == s[i] for i in range(3)):
                        # 6d and 8d are some columns, so can't have any digits in common
                        self.set_value((8, value), (6, 2 * value))

        for value in [i * i for i in range(10, 32)]:
            if 100 <= value <= 999 and '0' not in (s := str(value)) and len(set(s)) == 3:
                for clue in (3, 7, 10, 16):
                    self.set_value((clue, value))

        # 15a = 9/5 1a, and 2d = 14/5 1a,
        for value1 in range(105, 360, 10):
            value15 = value1 * 9 // 5
            value2 = value1 * 14 // 5
            s1, s15, s2 = str(value1), str(value15), str(value2)
            if '0' not in s1 + s15 + s2 and len(set(s1)) == len(set(s15)) == len(set(s2)) == 3:  # noqa: SIM102
                if s1[2] == s2[0] and len(set(s1 + s2)) == 5:
                    self.set_value((1, value1), (2, value2), (15, value15))

        seen_values = set()
        for power in range(3, 10):
            for base in itertools.count(2):
                value = base ** power
                if value >= 1000:
                    break
                if (value >= 100 and '0' not in (s := str(value)) and len(set(s)) == 3
                        and value not in seen_values):
                    self.set_value((9, value))
                    seen_values.add(value)

        for value in range(100, 1000):
            if ('0' not in (s := str(value)) and len(set(s)) == 3
                    and any(value % j == 0 for j in range(18, 73))):
                self.set_value((13, value))
                self.set_value((14, value))

        for row, column, value in itertools.product(range(1, 10), repeat=3):
            box = ((row - 1) // 3 * 3 + (column - 1) // 3) + 1
            constraints[f'r{row}c{column}={value}'] = [
                f'#r{row}c{column}', f'#r{row}v{value}', f'#c{column}v{value}',
                f'#b{box}v{value}',
                (f'xr{row}c{column}', str(value)),
                (f'xr{row}v{value}',  str(column)),
                (f'xc{column}v{value}', str(row)),
            ]

    def set_value(self, *clue_value_pairs: tuple[int, int], special=False):
        name = tuple((self.clue_named(str(clue_number)), value)
                     for clue_number, value in clue_value_pairs)
        value_options = [] if special else [f'value={value}' for _, value in clue_value_pairs]
        self.optional_constraints.update(value_options)
        first_clue_number = clue_value_pairs[0][0]
        clue_numbers = '/'.join(str(clue_number) for clue_number, _ in clue_value_pairs)
        constraint = [f'clue-{clue_numbers}', *value_options, ]

        if not special and first_clue_number in (13, 14):
            constraint[0] = '#' + constraint[0]
        seen = {}
        for clue_number, value in clue_value_pairs:
            clue = self.clue_named(str(clue_number))
            for char, square in zip(str(value), clue.locations, strict=True):
                if square in seen:
                    assert seen[square] == char
                else:
                    seen[square] = char
        constraint.extend((f'xr{r}c{c}', char) for (r, c), char in seen.items())
        constraint.extend((f'xr{r}v{char}', str(c)) for (r, c), char in seen.items())
        constraint.extend((f'xc{c}v{char}', str(r)) for (r, c), char in seen.items())
        self.constraints[name] = constraint

    def on_solve(self, solution: Sequence[Sequence[tuple[Clue, int]] | str]):
        clues: dict[Clue, int] = {}
        grid: dict[tuple[int, int], str] = {}
        for item in solution:
            if isinstance(item, tuple):
                clues.update(item)
            elif item.startswith('r'):
                row, column, value = int(item[1]), int(item[3]), item[5]
                grid[row, column] = value
        clue13, clue14 = self.clue_named('13'), self.clue_named('14')
        x1, x2 = clues[clue13], clues[clue14]
        t1 = sum(int(grid[i, i]) for i in range(1, 10))
        t2 = sum(int(grid[i, 10 - i]) for i in range(1, 10))
        if x1 % t1 == 0 and x2 % t2 == 0:
            self.print_it(grid)

    def print_it(self, grid: dict[tuple[int, int], str], **args):
        location_to_clue_numbers = {
            clue.location(0): [str(clue.name)] for clue in self.clue_list
        }
        self.draw_grid(max_row=10, max_column=10,
                       clued_locations=set(grid.keys()),
                       location_to_entry=grid,
                       location_to_clue_numbers=location_to_clue_numbers,
                       left_bars=set(itertools.product(range(1, 10), (4, 7))),
                       top_bars=set(itertools.product((4, 7), range(1, 10))),
                       **args)


def box72():
    squares = [169, 196, 256, 289, 324, 361, 529, 576, 625, 729, 784, 841, 961]
    for square10, square16 in itertools.permutations(squares, 2):
        str10, str16 = str(square10), str(square16)
        if str10[2] == str16[0] and len(set(str10 + str16)) == 5:
            unused = set("123456789") - set(str10) - set(str16)
            sorted_unused = ''.join(sorted(unused))
            print(square10, square16, sorted_unused)
            print("   ", end="")
            for i, j in itertools.permutations(sorted_unused, 2):
                value = int(i + j + str16[1])
                maybe_prime = value // 2
                text = f"{value}/{maybe_prime}"
                if not is_prime(maybe_prime):
                    style = "*"
                elif '0' in str(maybe_prime) or len(set(str(maybe_prime))) != 3:
                    style = "+"
                elif str(maybe_prime)[1] in str(value):
                    style = "/"
                else:
                    style = " "
                pprint(f"{escape(text)}{style}", end=" ")
            print()


def test_me():
    for i in (3, 4, 6, 7, 8):
        for j in (3, 4, 6, 7, 8):
            for k in (6, 8):
                if 3 not in (i, j, k):
                    continue
                if i == j:
                    continue
                p = is_prime(value := ((100 * i + 10 * j + k) // 2))
                print(value, 2 * value, p)


if __name__ == '__main__':
    # Listener4934.run()
    test_me()
