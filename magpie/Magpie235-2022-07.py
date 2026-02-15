import re
from collections import defaultdict
from itertools import combinations, product
from typing import Any

import numpy

from misc.primes import PRIMES
from solver import Clue, Clues, ConstraintSolver, EquationSolver
from solver import DancingLinks, KnownClueDict, KnownLetterDict

EQUATIONS = """
1 EGH
2 EHM
3 AGH
4 AHM
5 CGH
6 DHM
7 EGI
8 ABH
9 EKL
10 HIL
11 DFH
12 AEI
13 ADE
14 CGM
15 HJK
16 DEF
17 ABL
18 CDE
19 FIM
20 CEJ
21 CGI
22 DFL
23 ADK
24 ACI
25 BCF
26 ACD
"""


def get_equations():
    temp = EQUATIONS.strip().splitlines()
    values = [word[-3:] for word in temp]
    return values


GRID = """
XX.X.XXXX
X....X...
X...X....
X.X...X..
..X......
XX.X.X.X.
...X.X...
X....X...
..X......"""

ACROSSES = [(1, 7), (8, 4), (9, 4), (10, 6), (12, 4), (14, 3), (15, 5), (16, 3),
            (19, 4), (21, 6), (23, 4), (24, 4), (25, 7)]
DOWNS = [(2, 4), (3, 3), (4, 4), (5, 6), (6, 4), (7, 7), (10, 7), (11, 5), (13, 6),
         (17, 4), (18, 4), (20, 4), (22, 3)]


class MagpieSolver235Values(EquationSolver):
    @staticmethod
    def run():
        solver = MagpieSolver235Values()
        solver.solve(debug=True, max_debug_depth=1)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=PRIMES[:13])
        for a, b in combinations(clues, 2):
            self.add_constraint((a, b), lambda x, y: int(x) < int(y))

    def get_clues(self):
        values = get_equations()
        return [Clue(f"{n}", True, (n, 1), 1, expression=value)
                for n, value in enumerate(values, start=1)]

    def make_pattern_generator(self, clue: Clue, intersections: Any):
        regexp = f'.+'
        pattern = re.compile(regexp)
        return lambda _: pattern

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict):
        self.show_letter_values(known_letters)
        x = [int(clue.evaluators[0](known_letters)[0]) for clue in self._clue_list]
        print(x)


class SolverMagpie235Links (ConstraintSolver):
    @staticmethod
    def run():
        entries = (
            30, 42, 130, 182, 370, 434, 435, 598, 627, 638, 1054, 1131, 1209, 1295, 1558,
            1581, 3289, 3441, 3451, 4551, 5365, 5797, 7657, 13949, 14467, 14911)
        solver = SolverMagpie235Links(entries)
        solver.solve()

    def __init__(self, entries):
        clues = self.get_clues()
        super().__init__(clues)
        self.entry_table = self.build_entry_table(entries)
        self.encoding = self.create_encoding()

    def get_clues(self):
        clues = []
        grid = Clues.get_locations_from_grid(GRID)
        for (info, is_across) in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length in info:
                clue = Clue(f'{number}{letter}', letter == 'a',
                            base_location=grid[number - 1], length=length)
                clues.append(clue)
        return clues

    def solve(self):
        lines = defaultdict(list)
        for clue in self._clue_list:
            lines[clue.locations[0][not clue.is_across], clue.is_across].append(clue)
        location_to_clues = defaultdict(list)
        for clue in self._clue_list:
            for location in clue.locations:
                location_to_clues[location].append(clue)
        double_locations = {location for location, clues in location_to_clues.items()
                            if len(clues) > 1}
        constraints = {}
        optional_constraints = set()
        for (row_column, is_across), clues in lines.items():
            rc = "row" if is_across else "col"
            locations = [x for clue in clues for x in clue.locations]
            for base in range(2, 11):
                entries = [self.entry_table[base, clue.length] for clue in clues]
                for answers in product(*entries):
                    base_answers, real_answers = zip(*answers)
                    if len(set(real_answers)) != len(real_answers):
                        # Make sure no "real answer" is duplicated on a single row
                        continue
                    info = [f"{rc}-{row_column}", f"{rc}-Base-{base}"]
                    info.extend(f'Value-{x}' for x in real_answers)
                    # info.extend(f'Entry-{x}' for x in base_answers)
                    # optional_constraints.update(f'Entry-{x}' for x in base_answers)
                    if any(self.is_start_location(location) and digit == '0'
                          for location, digit in zip(locations, ''.join(base_answers))):
                        continue
                    for location, digit in zip(locations, ''.join(base_answers)):
                        if location in double_locations:
                            encoding = self.encoding[digit][is_across]
                            info.extend(f"{location[0]}-{location[1]}-{code}"
                                        for code in encoding)
                    constraints[(tuple(clues), tuple(base_answers))] = info

        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=self.my_printer)
        solver.solve(debug=100)

    def my_printer(self, output):
        clue_answers = {clue: value
                        for clues, base_values in output
                        for clue, value in zip(clues, base_values)}
        self.plot_board(clue_answers)

    def draw_grid(self, location_to_clue_numbers, **args: Any) -> None:
        super().draw_grid(location_to_clue_numbers={}, **args)

    @staticmethod
    def build_entry_table(entries):
        result = defaultdict(list)
        for entry in entries:
            for base in range(2, 11):
                value = numpy.base_repr(entry, base=base)
                result[base, len(value)].append((value, entry))
        return result

    @staticmethod
    def create_encoding():
        acrosses = list(combinations(range(5), 3))
        downs = [tuple(x for x in range(6) if x not in item) for item in acrosses]
        return {chr(ord('0') + i): (acrosses[i], downs[i]) for i in range(10)}

    @staticmethod
    def create_encoding_x():
        return {str(i) : (across, down)
                for i in range(10)
                for across in [[f"U{j}" if i == j else f"D{j}" for j in range(10)]]
                for down in [[f"D{j}" if i == j else f"U{j}" for j in range(10)]]
                }


if __name__ == '__main__':
    # MagpieSolver235Values.run()
    SolverMagpie235Links.run()
