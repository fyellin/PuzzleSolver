import random
import re
from datetime import datetime
from typing import Sequence, Dict, Set, Optional, Pattern

from solver import BaseSolver
from solver import Clue, Clues, ClueValue, Letter
from solver import EquationSolver, Intersection

primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101]

GRID = """
XX.XXX.X
X.X...X.
X.XX.X..
..X.X.X.
X......X
XX.X.XX.
X...X...
X.......
"""

ACROSS = """
A idiot
B h + i + g +h + w +a +y
C *********
F i+ t+ e + m + s
G en — dur(in + g) + m + e + l + o + d — y + m + a + n
M rain
O emits
P stig
T #####
U v
W aria
Z b + o +x + i + n + g
"""


DOWN = """
A sark
D pyx
E dine
F z +e +p + h + y +r
H m
I b
J q + u + i — nn
K wind
L mi + te + s
N nih
P ???
Q j — f + re
R lay + l + ady + lay
S aka
T dip
V (c + a)r + t + er
X s+ i + x + t + y — o — n — e
Y o — aa
"""

"""
A one-of-a-kind implementation.  We have clues, but don't know where they are going.

"""




ACROSS_LENGTHS = {
    2: 7, 7:8, 10:2, 11:3, 13:3, 14:6, 17:6, 19:3, 21:3, 23:2, 24:8, 26:7
}

DOWN_LENGTHS = {
    1:4, 17:4, 2:5, 20:2, 8:2, 14:5, 3:2, 12:3, 21:3, 4:3, 15:3, 25:2, 5:5, 22:2, 9:2, 16:5, 6:4, 18:4
}


def make_clue_list() -> Sequence[Clue]:
    clues = []
    locations = Clues.get_locations_from_grid(GRID)  # first location is index 0
    for is_across, lengths, suffix in ((True, ACROSS_LENGTHS, 'a'), (False, DOWN_LENGTHS, 'd')):
        for i, length in lengths.items():
            clue = Clue(str(i) + suffix, is_across, locations[i - 1], length)
            clues.append(clue)
    return clues


def make_expressions() -> Sequence[Clue]:
    clues = []
    for line in CLUES.splitlines():
        name = line[0]
        expression = line[2:]
        expression = re.sub(r"([A-Z])(\d)", r"(\1**\2)", expression)
        clue = Clue(name, True, (0, 0), 1, expression=expression)
        clues.append(clue)
    return tuple(clues)


class Magpie017Solver(BaseSolver):
    expressions: Sequence[Clue]
    missing_variables: Dict[Clue, Set[Letter]]
    step_count: int
    solution_count: int
    debug: bool

    def __init__(self, clue_list: Sequence[Clue], expressions: Sequence[Clue]) -> None:
        super().__init__(clue_list)
        self.expressions = expressions
        return
        self.missing_variables = {
            # TODO(fy): Fix me.  We know that all clue.evaluators have length 1
            clue: set(evaluator_vars) - {clue.name}
            for clue in self.expressions for (_, evaluator_vars) in clue.evaluators
        }

    def solve(self, *, show_time: bool = True, debug: bool = False, max_debug_depth: Optional[int] = None) -> int:
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
        clues_to_try = [clue for clue in self._clue_list if clue not in known_clues]
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
        EquationSolver(self._clue_list).show_solution(known_clues, known_letters)

    def make_runtime_pattern(self, clue: Clue, known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
        pattern_list = [self.get_allowed_regexp(location) for location in clue.locations]
        pattern_list.append('$')
        for other_clue, other_clue_value in known_clues.items():
            intersections = Intersection.get_intersections(clue, other_clue)
            for intersection in intersections:
                pattern_list[intersection.this_index] = other_clue_value[intersection.other_index]
        return re.compile(''.join(pattern_list))


def run() -> None:
    clue_list = make_clue_list()
    # expressions = make_expressions()
    solver = Magpie017Solver(clue_list, None)


if __name__ == '__main__':
    run()
