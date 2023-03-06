import itertools
import math
from collections.abc import Sequence
from functools import cache

from misc.factors import divisor_count
from solver import Clue, Clues, ConstraintSolver, generators
from solver.constraint_solver import Constraint, KnownClueDict
from solver.generators import fibonacci, known, palindrome, prime, square, \
    square_pyramidal_generator, triangular


@cache
def DS(number: int | str) -> int:
    return sum(int(x) for x in str(number))


@cache
def DP(number: int | str) -> int:
    return math.prod(int(x) for x in str(number))


@cache
def MP(number: int | str) -> int:
    for count in itertools.count(1):
        number = DP(number)
        if number < 10:
            return count


HAPPY = {1, 7, 10, 13, 19, 23, 28, 31, 32, 44, 49, 68, 70, 79, 82, 86, 91, 94, 97, }
LUCKY = {1, 3, 7, 9, 13, 15, 21, 25, 31, 33, 37, 43, 49,
         51, 63, 67, 69, 73, 75, 79, 87, 93, 99, }
TRIANGULAR = {x * (x + 1) // 2 for x in range(1, 100)}
SQUARE = {x * x for x in range(1, 100)}
CUBE = {x * x * x for x in range(1, 100)}
TWO_POWER = {2 ** x for x in range(0, 10)}


GRID = """
XX.XXXX
X.XX.X.
X...XX.
XXX.X.X
X..XXX.
XXX..XX
.X..X..
"""


def generator14a(clue):
    for digits in itertools.combinations('13579', clue.length):
        x = ''.join(digits)
        if DP(x) in TRIANGULAR:
            yield x
            yield x[::-1]


LETTERS = ['jt', 'aku', 'blv', 'cmw', 'dnx', 'eoy', 'fpz', 'gq', 'hr', 'is']


ACROSSES = [
    (1, 3, triangular, Constraint('1a', lambda x: DP(x) in TRIANGULAR)),
    (3, 3, square, Constraint('3a', lambda x: DS(x) in SQUARE)),
    (7, 2, Constraint('7a 21d', lambda x, y: DS(x) * 2 == int(y))),
    (9, 2, Constraint('9a 18d', lambda x, y: int(x) == 26 + int(y))),
    (10, 2, palindrome),
    (11, 4, Constraint('11a 21d', lambda x, y: DS(x) == int(y))),
    (13, 2, Constraint('13a', lambda x: (ord(x[0]) + ord(x[1])) % 2 != 0),
            Constraint('13a', lambda x: DP(x) > 9)),
    (14, 3, generator14a),
    (17, 3, Constraint('17a', lambda x: DS(x) in TRIANGULAR)),
    (19, 2, Constraint('19a 21d', lambda x, y: DP(x) == int(y))),
    (20, 4, prime, Constraint('20a', lambda x: DP(x) in SQUARE),
            Constraint('20a 13d', lambda x, y: int(y) % DS(x) == 0)),
    (23, 2, prime, Constraint('23a', lambda x: x[0] == x[1])),
    (25, 2, prime),
    (26, 2, Constraint('26a', lambda x: DP(x) in CUBE)),
    (28, 3, Constraint('28a', lambda x: DP(x) == 180)),
    (29, 3, Constraint('29a', lambda x: DP(x) in CUBE),
            Constraint('29a 21d', lambda x, y: DS(x) == int(y))),
]

DOWNS = [
    (1, 2, Constraint('1d', lambda x: (DS(x) + DP(x)) % 10 == 5)),
    (2, 3, palindrome, Constraint('2d', lambda x: int(x) % 5 == 0 and MP(x) == 2)),
    (3, 3, Constraint('3d 3a', lambda x, y: abs(int(x) - int(y)) == 3)),
    (4, 2, Constraint('4d 8d', lambda x, y: int(x) > int(y)),
           Constraint('4d', lambda x: DS(x) > 9)),
    (5, 2, known(*(2 * x * x for x in range(1, 10)))),
    (6, 3, Constraint('6d', lambda x: divisor_count(int(x)) == 8)),
    (8, 2, square_pyramidal_generator),
    (11, 2, square),
    (12, 2, Constraint('12d', lambda x: DP(x) in {0, 2, 4, 6, 8})),
    (13, 2, Constraint('13d', lambda x: int(x) % 7 == 0)),
    (15, 2, Constraint('15d', lambda x: DP(x) > 9)),
    (16, 2, prime),
    (18, 2, known(*(LUCKY & HAPPY))),
    (19, 3, Constraint('19d', lambda x: DP(x) > 9)),
    (20, 3, Constraint('20d 21d', lambda x, y: (DP(x) + DS(x)) % int(y) == 0)),
    (21, 2, Constraint('21d', lambda x: int(x) % 10 == 0)),
    (22, 3, Constraint('22d', lambda x: DP(x) in TWO_POWER)),
    (24, 2, Constraint('24d', lambda x: DP(x) in SQUARE)),
    (25, 2, known(*LUCKY)),
    (27, 2, fibonacci),
]


class Listener4751 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Listener4751()
        solver.solve(debug=False)

    def __init__(self) -> None:
        self.results = []
        self.message = self.translate("REVERSE ACROSS ENTRIES".replace(' ', ''))
        clues, constraints = self.get_clues()
        self.constraints = constraints
        super().__init__(clues, constraints=constraints,)

    def translate(self, message):
        return tuple((ord(x) - 64) % 10 for x in message)

    def get_clues(self) -> tuple[Sequence[Clue], Sequence[Constraint]]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        constraints = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length, *stuff in information:
                clue_name = f'{number}{letter}'
                generator = generators.allvalues
                if stuff and not isinstance(stuff[0], Constraint):
                    generator = stuff.pop(0)
                for constraint in stuff:
                    assert isinstance(constraint, Constraint), clue_name
                    assert clue_name == constraint.clues.split()[0], clue_name
                    constraints.append(constraint)
                location = grid[number - 1]
                clue = Clue(clue_name, is_across, location, length,
                            generator=generator or generators.allvalues)
                clues.append(clue)
        return clues, constraints

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        values = {int(x) for x in known_clues.values()}
        expected_values = {
            DP(known_clues[self.clue_named('13a')]),
            DS(known_clues[self.clue_named('4d')]),
            DP(known_clues[self.clue_named('15d')]),
            DP(known_clues[self.clue_named('19d')]),
        }
        return expected_values <= values

    def show_solution(self, result: KnownClueDict) -> None:
        self.results.append(result.copy())
        message = self.clue_to_message(result)
        if message == self.message:
            count = len(self.results)
            alt_result = self.reverse_solution(result)
            if self.verify_solution(alt_result):
                self.plot_board(result, subtext=f"Solution #{count}")
                self.plot_board(alt_result, subtext=f"Entry #{count}")

    def clue_to_message(self, result):
        return tuple(int(result[clue][-1]) for clue in self._clue_list
                     if not clue.is_across)

    def reverse_solution(self, known_clues: KnownClueDict) -> KnownClueDict:
        locations1 = {location: value
                      for clue in self._clue_list if not clue.is_across
                      for location, value in zip(clue.locations, known_clues[clue])}
        locations2 = {location: value
                      for clue in self._clue_list if clue.is_across
                      for location, value in zip(clue.locations, known_clues[clue][::-1])}
        locations = locations1 | locations2
        result = {clue: ''.join(locations[location] for location in clue.locations)
                  for clue in self._clue_list}

        return result

    def verify_solution(self, known_clues: KnownClueDict) -> bool:
        if len(set(known_clues.values())) != len(known_clues):
            return False
        if any(value[0] == '0' for value in known_clues.values()):
            return False
        for clue, value in known_clues.items():
            legal_values = self.__get_clue_legal_values(clue)
            if value not in legal_values and int(value) not in legal_values:
                return False
        for constraint in self.constraints:
            values = [known_clues[self.clue_named(x)] for x in constraint.clues.split()]
            if not constraint.predicate(*values):
                return False
        return True

    @cache
    def __get_clue_legal_values(self, clue):
        return set(clue.generator(clue))


if __name__ == '__main__':
    Listener4751.run()
