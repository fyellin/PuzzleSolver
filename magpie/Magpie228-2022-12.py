import re
from collections import Counter
from itertools import permutations
from typing import Any

from solver import Clue, ClueValue, Clues, ConstraintSolver, Letter, Location, generators
from solver.constraint_solver import LetterCountHandler

GRID = """
XXXXXX
X.X...
X..XX.
X.XX..
XX..XX
X.X...
"""

ACROSSES = """
1 Min DL^N (4)
5 Max GN (2)
7 Max R – M (2)
8 * * (4)
9 Min L^G (3)
10 Min DNR (3)
12 * * (3)
14 * * (3)
15 Min L^U (4)
17 Max DM (2)
19 Min (L^L)O (2)
20 * * (4)
"""

DOWNS = """
1 * * (2)
2 Min O^O (4)
3 Max BU (3)
4 * * (3)
5 Min D^D (2)
6 Min BBE (4)
9 Max N^D (4)
11 Max BEM (4)
13 * * (3)
14 * * (3)
16 Max EL (2)
18 Max GU (2)
"""


class Magpie288(ConstraintSolver):
    letter_values: dict[Letter, int]

    @staticmethod
    def run():
        solver = Magpie288()
        # solver.plot_board({})
        solver.verify_is_180_symmetric()
        solver.solve(debug=True)

    def __init__(self):
        clue_list = self.get_clues()
        super().__init__(clue_list, letter_handler=self.MyLetterCountHandler())
        # self.letter_values = self.get_letter_values()
        # print(self.letter_values)
        self.letter_values = {'B': 19, 'D': 3, 'E': 23, 'G': 7, 'L': 2,
                              'M': 17, 'N': 11, 'O': 5, 'R': 29, 'U': 13}

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        result: list[Clue] = []
        for lines, is_across, letter in ((ACROSSES, True, 'a'), (DOWNS, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (Min|Max|\*) (.*) \((\d+)\)', line)
                number = int(match.group(1))
                location = locations[number - 1]
                if match.group(2) == '*':
                    clue = Clue(f'{number}{letter}', is_across, location, int(match.group(4)),
                                generator=self.generator)
                else:
                    assert match.group(2) in {'Min', 'Max'}
                    clue = Clue(f'{number}{letter}', is_across, location, int(match.group(4)),
                                expression=match.group(3).strip(), context=match.group(2).strip(),
                                generator=self.generator)
                result.append(clue)
        return result

    def get_letter_values(self) -> dict[Letter, int]:
        # The evaluation must be < the the second number
        clue_min = [(clue.evaluators[0], 10 ** clue.length, clue.expression)
                    for clue in self._clue_list if clue.context == 'Min']
        # The evaluation must be >= the second number.  For say, an 4-digit maximum, the smallest possible
        # maximum is 10,000 leaving space for precisely one answer.  But all answers are prime, so the smallest
        # possible maximum is actually 10,001.
        clue_max = [(clue.evaluators[0], 10 ** (clue.length - 1) + 1, clue.expression)
                    for clue in self._clue_list if clue.context == 'Max']
        for (b, d, e, g, l, n, o, r, m, u) in permutations((2, 3, 5, 7, 11, 13, 17, 19, 23, 29)):
            if r < m:
                continue
            info: dict[Letter, int] = dict(B=b, D=d, E=e, G=g, L=l, M=m, N=n, O=o, R=r, U=u)
            if all(int(evaluator(info)) < maximum for evaluator, maximum, _ in clue_min):
                if all(int(evaluator(info)) >= minimum for evaluator, minimum, _ in clue_max):
                    return info

    def generator(self, clue: Clue):
        if not clue.context:
            def my_filter(_):
                return True
        else:
            value = int(clue.evaluators[0](self.letter_values)[0])
            if clue.context == 'Min':
                def my_filter(x):
                    return x >= value
            else:
                def my_filter(x):
                    return x <= value
        return filter(my_filter, generators.prime(clue))

    def get_allowed_regexp(self, location: Location) -> str:
        if not self.is_start_location(location):
            return '.'
        clues = [clue for clue in self._clue_list if clue.location(0) == location and clue.context]
        if not clues:
            return '.'
        result = set(range(1, 10))
        for clue in clues:
            min_max_value = clue.evaluators[0](self.letter_values)[0]
            if clue.context == 'Min':
                assert len(min_max_value) <= clue.length
                if len(min_max_value) == clue.length:
                    result.intersection_update(range(int(min_max_value[0]), 10))
            else:
                assert len(min_max_value) >= clue.length
                if len(min_max_value) == clue.length:
                    result.intersection_update(range(1, int(min_max_value[0]) + 1))
        return '[' + ''.join(str(x) for x in sorted(result)) + ']'

    class MyLetterCountHandler(LetterCountHandler):
        def real_checking_value(self, value: ClueValue, info: Any) -> bool:
            count1 = sum(1 for x in self._counter.values() if x > 0)
            count2 = max(self._counter.values())
            result = (count1 <= 9 and count2 <= 4) or (count1 <= 6 and count2 <= 6) \
                     or (count1 <= 4 and count2 <= 9) or (count1 <= 3 and count2 <= 12)
            return result

if __name__ == '__main__':
    Magpie288.run()
