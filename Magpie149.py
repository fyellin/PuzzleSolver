"""
A one-of-a-kind implementation.  We have clues, but don't know where they are going.

"""

import random
import re
from datetime import datetime
from typing import Sequence, Dict, Set, Optional

from Clue import Clue, ClueList, ClueValue, Letter
from GenericSolver import Intersection, BaseSolver

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
    clues = []
    for i in range(1, len(LENGTHS)):
        clue = Clue(str(i), i in ACROSSES, locations[i], LENGTHS[i])
        clues.append(clue)
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


class SolverByClue(BaseSolver):
    expressions: Sequence[Clue]
    missing_variables: Dict[Clue, Set[str]]
    count_total: int
    debug: bool

    def __init__(self, clue_list: ClueList, expressions: Sequence[Clue]) -> None:
        super(SolverByClue, self).__init__(clue_list)
        self.expressions = expressions
        self.missing_variables = {
            clue: set(x for x in clue.expression if 'A' <= x <= 'Z' and x != clue.name)
            for clue in self.expressions
        }

    def solve(self, *, show_time: bool = True, debug: bool = False) -> None:
        self.count_total = 0
        self.debug = debug
        time1 = datetime.now()
        self.__solve({}, {})
        time2 = datetime.now()
        if show_time:
            print(f'Steps: {self.count_total};  {time2 - time1}')

    def __solve(self, known_letters: Dict[Letter, int], known_clues: Dict[Clue, ClueValue]) -> None:
        depth = len(known_letters)
        if len(known_letters) == 25:
            print(known_clues)
            self.clue_list.plot_board(known_clues)
            return

        known_letters_set = set(known_letters.keys())
        expressions_to_try = [expression for expression in self.expressions
                              if expression.name not in known_letters_set
                              if self.missing_variables[expression].issubset(known_letters_set)]
        clues_to_try = [clue for clue in self.clue_list if clue not in known_clues]
        clue_to_pattern = {clue: Intersection.make_runtime_pattern(clue, known_clues, self)
                           for clue in clues_to_try}

        def get_legal_value(expression: Clue, clue: Clue) -> Optional[ClueValue]:
            known_letters[Letter(expression.name)] = int(clue.name)
            value = expression.eval(known_letters)
            del known_letters[Letter(expression.name)]
            if value and clue_to_pattern[clue].fullmatch(value):
                return value
            return None

        self.count_total += len(clues_to_try) * len(expressions_to_try)
        next_steps = {expression: [(clue, value) for clue in clues_to_try
                                   for value in [get_legal_value(expression, clue)]
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
            self.__solve(known_letters, known_clues)
            del known_letters[Letter(expression.name)]
            del known_clues[clue]


def run() -> None:
    clue_list = make_clue_list()
    expressions = make_expressions()
    solver = SolverByClue(clue_list, expressions)
    solver.solve()


if __name__ == '__main__':
    run()
