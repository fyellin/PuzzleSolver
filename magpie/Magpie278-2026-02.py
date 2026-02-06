from collections import Counter
from typing import Any

from misc.primes import PRIMES
from solver import ClueValue, Clues, ConstraintSolver, Location
from solver.constraint_solver import Constraint, KnownClueDict, LetterCountHandler
from solver.generators import allvalues, prime, square, triangular

ACROSS_LENGTHS = "33/231/132/33"
DOWN_LENGTHS = "13/31/22/22/13/31"

class Magpie278(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        for clue in clues:
            clue.generator = allvalues
        clue_map = {clue.name: clue for clue in clues}
        clue_map['4a'].generator = triangular
        clue_map['12a'].generator = prime
        clue_map['14a'].generator = square
        clue_map['4d'].generator = square

        constraints = [
            Constraint('7a', lambda x: x[0] < x[1] < x[2]),
            Constraint('8d', lambda x: x[0] < x[1] < x[2]),
            Constraint('5d', lambda x: sum(int(d) for d in x) in PRIMES),
            Constraint("6a 11d", lambda x, y: set(x).isdisjoint(set(y))),
            Constraint("9a 13a", lambda x, y: sorted(x) == sorted(y)),
            Constraint("10d 3d", lambda x, y: int(x) % int(y) == 0),
            Constraint("2d 6d", lambda x, y: int(y) % sum(int(a) for a in x) == 0),
        ]
        super().__init__(clues, constraints=constraints, letter_handler=MyLetterHandler())
        self.one_across = self.clue_named('1a')

    def get_allowed_regexp(self, location: Location) -> str:
        return '[1-9]'

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        grid = {location: int(char) for clue, value in known_clues.items()
                for location, char in zip(clue.locations, value)}
        counter = Counter(grid.values())
        if sum(counter.keys()) != 24:
            return False
        expected_one_across = sum(key * value for key, value in counter.items())
        if expected_one_across != int(known_clues[self.one_across]):
            return False
        return set(counter.keys()) == set(counter.values())


class MyLetterHandler(LetterCountHandler):
    def real_checking_value(self, value: ClueValue, info: Any) -> bool:
        total = sum(int(key) for key, value in self._counter.items() if value > 0)
        return total <= 24


if __name__ == '__main__':
    Magpie278().run()
