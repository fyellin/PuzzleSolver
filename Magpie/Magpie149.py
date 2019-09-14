"""
A one-of-a-kind implementation.  We have clues, but don't know where they are going.

"""

import random
import re
from datetime import datetime
from typing import Sequence, Dict, Set, Optional, Pattern

from Clue import Clue, ClueList, ClueValue, Letter
from GenericSolver import BaseSolver, EquationSolver
from Intersection import Intersection

GRID = """
XXXXX.X
XX.XX..
X.XX...
X...XXX
XX..X..
X..XX..
X...X...
"""

LENGTHS = (0, 3, 4, 2, 4, 5, 3, 3, 3, 5, 3,
           3, 5, 3, 3, 3, 4, 3, 3, 3, 3,
           3, 3, 2, 4, 3)

ACROSSES = (1, 4, 8, 10, 11, 13, 14, 15, 19, 20, 21, 22, 24, 25)

CLUES = """A A2 + Z
B B2J – BJ
C C2R
D DT
E E2R + Z
F F5
G GMY
H HIM
I I3L
J J3F3
K K3 – K
L L4 + L
M M2F + P
N N2 + HN
P PQV
Q QW
R R9D
S S2H2
T TN
U U4
V V2 + V
W WL
X XRW
Y Y2 + S
Z ZU"""


def make_clue_list() -> ClueList:
    lines = GRID.splitlines()
    lines = [line for line in lines if line]
    locations = [(0, 0)]
    for row, line in enumerate(lines):
        for column, item in enumerate(line):
            if item == 'X':
                locations.append((row + 1, column + 1))
    clues = [Clue(str(i), i in ACROSSES, locations[i], LENGTHS[i]) for i in range(1, len(LENGTHS))]
    clue_list = ClueList(clues)
    clue_list.verify_is_180_symmetric()
    return clue_list


def make_expressions() -> Sequence[Clue]:
    clues = []
    for line in CLUES.splitlines():
        name = line[0]
        expression = line[2:]
        expression = re.sub(r"([A-Z])(\d)", r"(\1**\2)", expression)
        clue = Clue(name, True, (0, 0), 1, expression=expression)
        clues.append(clue)
    return tuple(clues)


class Magpie149Solver(BaseSolver):
    expressions: Sequence[Clue]
    missing_variables: Dict[Clue, Set[Letter]]
    step_count: int
    solution_count: int
    debug: bool

    def __init__(self, clue_list: ClueList, expressions: Sequence[Clue]) -> None:
        super().__init__(clue_list)
        self.expressions = expressions
        self.missing_variables = {
            # TODO(fy): Fix ME
            clue: set(evaluator_vars) - {clue.name}
            for clue in self.expressions for (_, evaluator_vars) in clue.evaluators
        }

    def solve(self, *, show_time: bool = True, debug: bool = False) -> int:
        self.step_count = 0
        self.solution_count = 0
        self.debug = debug
        time1 = datetime.now()
        self.__solve({}, {})
        time2 = datetime.now()
        if show_time:
            print(f'Solutions { self.solution_count}; Steps: {self.step_count};  {time2 - time1}')
        return self.solution_count

    def __solve(self, known_clues: Dict[Clue, ClueValue], known_letters: Dict[Letter, int]) -> None:
        depth = len(known_letters)
        if len(known_letters) == 25:
            self.show_solution(known_clues, known_letters)
            self.solution_count += 1
            return

        known_letters_set = set(known_letters.keys())
        expressions_to_try = [expression for expression in self.expressions
                              if expression.name not in known_letters_set
                              if self.missing_variables[expression].issubset(known_letters_set)]
        clues_to_try = [clue for clue in self.clue_list if clue not in known_clues]
        clue_to_pattern = {clue: self.make_runtime_pattern(clue, known_clues)
                           for clue in clues_to_try}

        def get_value_if_fits(expression: Clue, clue: Clue) -> Optional[ClueValue]:
            known_letters[Letter(expression.name)] = int(clue.name)
            evaluator = expression.evaluators[0]
            value = evaluator(known_letters)
            del known_letters[Letter(expression.name)]
            if value and clue_to_pattern[clue].fullmatch(value):
                return value
            return None

        self.step_count += len(clues_to_try) * len(expressions_to_try)
        next_steps = {expression: [(clue, value) for clue in clues_to_try
                                   for value in [get_value_if_fits(expression, clue)]
                                   if value]
                      for expression in expressions_to_try}
        expression, clue_value_pairs = min(next_steps.items(),
                                           key=lambda x: (len(x[1]), x[0].length, random.random()))
        if not clue_value_pairs:
            if self.debug:
                print(f'{" | " * depth}{expression.name}: XXXX')
            return

        for i, (clue, value) in enumerate(clue_value_pairs):
            if self.debug:
                print(f'{" | " * depth}{expression.name} {i + 1}/{len(clue_value_pairs)}: {clue.name}:{value} -->')
            known_letters[Letter(expression.name)] = int(clue.name)
            known_clues[clue] = value
            self.__solve(known_clues, known_letters)
            del known_letters[Letter(expression.name)]
            del known_clues[clue]

    def show_solution(self, known_clues: Dict[Clue, ClueValue], known_letters: Dict[Letter, int]) -> None:
        EquationSolver(self.clue_list).show_solution(known_clues, known_letters)

    def make_runtime_pattern(self, clue: Clue, known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
        pattern_list = [self.clue_list.get_allowed_regexp(location) for location in clue.locations()]
        pattern_list.append('$')
        for other_clue, other_clue_value in known_clues.items():
            intersections = Intersection.get_intersections(clue, other_clue)
            for intersection in intersections:
                pattern_list[intersection.this_index] = other_clue_value[intersection.other_index]
        return re.compile(''.join(pattern_list))


def run() -> None:
    clue_list = make_clue_list()
    expressions = make_expressions()
    solver = Magpie149Solver(clue_list, expressions)
    solver.solve()


if __name__ == '__main__':
    run()
