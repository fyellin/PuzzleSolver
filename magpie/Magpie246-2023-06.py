import itertools
from collections import defaultdict
from collections.abc import Sequence
from functools import cache
from typing import Any

from solver import Clue, Clues, Constraint, ConstraintSolver, DancingLinks, Location, \
    generators, KnownClueDict
from solver.generators import cube, palindrome, prime, square, triangular

GRID = """
XXXXXX
X..X..
X.XX.X
X.XXX.
.X.XX.
X...X.
"""

ACROSSES = [
    (1, 2),
    (3, 3, square),
    (7, 3),
    (8, 3, cube),  # 21a
    (9, 3),
    (11, 3),
    (13, 2),
    (14, 2, triangular),  # 17d
    (16, 2),
    (17, 2, cube),
    (18, 2),
    (20, 3, prime),
    (21, 2, Constraint('21a 8a', lambda x, y: int(y) % int(x) == 0))
]

DOWNS = [
    (1, 5, Constraint('1d', lambda x: len(set(x)) == 5)),
    (2, 4),
    (3, 2, Constraint('3d 19d', lambda x, y: int(x) % int(y) == 0)),
    (4, 2, Constraint('4d 6d', lambda x, y: x == y[::-1])),
    (5, 4),
    (6, 2),
    (10, 4),
    (12, 3),
    (15, 3, palindrome),
    (17, 2, Constraint('17d 14a', lambda x, y: x == y[::-1])),
    (19, 2, Constraint('19d 14a', lambda x, y: int(y) % int(x) == 0)) # 3d
]

UNUSED_CLUES = ['1a', '7a', '9a', '11a', '13a', '16a', '18a', '1d', '2d', '5d', '10d', '12d']
UNUSED_CLUES += ['20a']

class Magpie246 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie246()
        solver.solve(debug=False)
        # solver.plot_board()

    def __init__(self) -> None:
        clues, constraints = self.get_clues()
        self.summary = defaultdict(set)
        super().__init__(clues, constraints=constraints)

    def solve(self, **args):
        super().solve(**args)
        solutions = self.dancing_links()
        for solution in solutions:
            self.plot_board(None, solution=solution)

    def get_allowed_regexp(self, location: Location) -> str:
        return '[123456]'

    def get_clues(self) -> tuple[Sequence[Clue], Sequence[Constraint]]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        constraints = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length, *stuff in information:
                clue_name = f'{number}{letter}'
                generator = None
                if stuff and not isinstance(stuff[0], Constraint):
                    generator = stuff.pop(0)
                for constraint in stuff:
                    assert isinstance(constraint, Constraint), clue_name
                    assert clue_name == constraint.clues.split()[0], clue_name
                    constraints.append(constraint)
                generator = None if clue_name in UNUSED_CLUES else (generator or generators.allvalues)
                location = grid[number - 1]
                clue = Clue(clue_name, is_across, location, length, generator=generator)
                clues.append(clue)
        return clues, constraints

    def show_solution(self, known_clues: KnownClueDict) -> None:
        if len(self.summary) == 0:
            super().show_solution(known_clues)
        for clue, value in known_clues.items():
            for location, digit in zip(clue.locations, value):
                self.summary[location].add(int(digit))

    def draw_grid(self, location_to_entry, solution=None, **args: Any) -> None:
        if solution is not None:
            location_to_entry = solution
        colors = ['pink', 'lightblue', 'lightgreen', 'yellow', 'white', 'lightgray']
        shading = {location: colors[int(value) - 1]
                   for location, value in location_to_entry.items()}

        super().draw_grid(shading=shading, location_to_entry=location_to_entry, **args)

    def dancing_links(self):
        chains = self.get_all_chains()
        chains_by_digit = {i: chains.copy() for i in range(1, 7)}
        for square, digits in self.summary.items():
            for digit in range(1, 7):
                if digit not in digits:
                    chains_by_digit[digit] = {x for x in chains_by_digit[digit] if square not in x}
                elif len(digits) == 1:
                    chains_by_digit[digit] = {x for x in chains_by_digit[digit] if square in x}
        constraints = {}
        for digit in range(1, 7):
            for chain in chains_by_digit[digit]:
                constraints[digit, chain] = [*(f'Square={x}' for x in chain), f'Value={digit}']

        solutions = []

        def row_printer(solution):
            locations = {location: str(digit)
                         for digit, locations in solution for location in locations}
            solutions.append(locations)

        solver = DancingLinks(constraints, row_printer=row_printer)
        solver.solve()
        return solutions

    def dancing_links_alt(self):
        chains = self.get_all_chains()
        chains_by_digit = {i: chains.copy() for i in range(1, 7)}
        placed = {}
        for square, digits in self.summary.items():
            for digit in range(1, 7):
                if digit not in digits:
                    chains_by_digit[digit] = {x for x in chains_by_digit[digit] if square not in x}
                elif len(digits) == 1:
                    chains_by_digit[digit] = {x for x in chains_by_digit[digit] if square in x}
                    placed[square] = digit

        for digit in range(1, 7):
            chains_by_digit[digit] = {x - frozenset(placed.keys()) for x in chains_by_digit[digit]}

        changed = True
        while changed:
            changed = False
            for digit, chains in chains_by_digit.items():
                common = frozenset.intersection(*chains)
                if common:
                    placed.update((square, digit) for square in common)
                    print(f'{digit} must be placed in {common}')
                    for digit2, chains2 in chains_by_digit.items():
                        if digit2 != digit:
                            old_length = len(chains2)
                            chains_by_digit[digit2] = {x for x in chains2 if common.isdisjoint(x)}
                            new_length = len(chains_by_digit[digit2])
                            if old_length != new_length:
                                changed = True
                                print(f". . . Chains for {digit2} went {old_length} -> {new_length}")
                        else:
                            chains_by_digit[digit2] = {x - common for x in chains}

            square_by_digit = defaultdict(set)
            for digit, chains in chains_by_digit.items():
                for chain in chains:
                    for square in chain:
                        square_by_digit[square].add(digit)
            for square, digits in square_by_digit.items():
                if len(digits) == 1:
                    digit = digits.pop()
                    print(f"Only digit {digit} can accomodate {square}")
                    old_length = len(chains_by_digit[digit])
                    placed[square] = digit
                    chains_by_digit[digit] = {x - {digit} for x in chains_by_digit[digit] if square in x}
                    new_length = len(chains_by_digit[digit])
                    changed = True
                    print(f".... {old_length} -> {new_length}")

        return [placed]


    @staticmethod
    def get_all_chains():
        @cache
        def neighbor(point):
            r, c = point
            results = []
            for dr, dc in itertools.product((1, -1), repeat=2):
                for ddr, ddc in (dr, 2 * dc), (2 * dr, dc):
                    if 1 <= r + ddr <= 6 and 1 <= c + ddc <= 6:
                        results.append(((r + ddr), (c + ddc)))
            return results

        def add_internal(seen):
            if len(seen) == 6:
                yield seen
            else:
                for next in neighbor(seen[-1]):
                    if next not in seen:
                        next_chain = (*seen, next)
                        yield from add_internal(next_chain)

        def get_chains():
            seen = set()
            for i, j in itertools.product(range(1, 7), repeat=2):
                for value in add_internal(((i, j),)):
                    seen.add(frozenset(value))
            special_set = frozenset([(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)])
            return  {x for x in seen if len(x & special_set) <= 1}

        return get_chains()

if __name__ == '__main__':
    # pass
    Magpie246.run()
