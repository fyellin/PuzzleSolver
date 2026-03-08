import re
from collections import defaultdict
from itertools import combinations, islice, product
from typing import Any

import numpy
from more_itertools import sieve

from solver import (
    Clue,
    Clues,
    ConstraintSolver,
    DancingLinks,
    EquationSolver,
    KnownClueDict,
    KnownLetterDict,
)
from solver.dancing_links import get_row_column_optional_constraints

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


ACROSS_LENGTHS = "711/414/6111/4113/11511/3114/1116/414/117"
DOWN_LENGTHS = "117/414/1116/3114/11511/4113/6111/414/711"


class MagpieSolver235Values(EquationSolver):
    @staticmethod
    def run():
        solver = MagpieSolver235Values()
        solver.solve(debug=True, max_debug_depth=1)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, islice(sieve(100), 13))
        for a, b in combinations(clues, 2):
            self.add_constraint((a, b), lambda x, y: int(x) < int(y))

    def get_clues(self):
        values = get_equations()
        return [Clue(f"{n}", True, (n, 1), 1, expression=value)
                for n, value in enumerate(values, start=1)]

    def make_pattern_generator(self, clue: Clue, intersections: Any):
        regexp = r'.+'
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
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues)
        self.verify_is_four_fold_symmetric()
        self.entry_table = self.build_entry_table(entries)

    def solve(self):
        constraints = {}
        optional_constraints = get_row_column_optional_constraints(9, 9)
        optional_constraints.update(f'Base-{base}->{rc}'
                                    for base in range(2, 11) for rc in ('row', 'column'))
        optional_constraints.update(f'{rc}-{number}->base'
                                    for number in range(1, 10) for rc in ('Row', 'Column'))
        for clue in self._clue_list:
            for value, entry, base in self.entry_table[clue.length]:
                constraint = [f'Value-{entry}', clue.name,
                              *clue.dancing_links_rc_constraints(value)
                              ]
                row, column = clue.base_location
                # Each base gets a single row/column.  Each row/column gets a single base
                if clue.is_across:
                    constraint.append((f'Base-{base}->row', row))
                    constraint.append((f'Row-{row}->base', base))
                else:
                    constraint.append((f'Base-{base}->column', column))
                    constraint.append((f'Column-{column}->base', base))
                constraints[clue, value, entry, base] = constraint

        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=self.my_printer)
        solver.solve(debug=100)

    def my_printer(self, output):
        clue_answers = {clue: value for clue, value, _entry, _base in output}
        self.plot_board(clue_answers)

    def draw_grid(self, location_to_clue_numbers, **args: Any) -> None:
        super().draw_grid(location_to_clue_numbers={}, **args)

    @staticmethod
    def build_entry_table(entries):
        result = defaultdict(list)
        for entry in entries:
            for base in range(2, 11):
                value = numpy.base_repr(entry, base=base)
                result[len(value)].append((value, entry, base))
        return result

if __name__ == '__main__':
    # MagpieSolver235Values.run()
    SolverMagpie235Links.run()
