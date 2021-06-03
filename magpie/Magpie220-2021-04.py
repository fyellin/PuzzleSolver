import collections
import itertools
import math
from typing import Sequence, Iterator, Any

import solver
from solver import generators, ConstraintSolver, Clues, Clue, ClueValue
from solver.constraint_solver import KnownClueDict

GRID = """
XXX.
.X.X
XXX.
X.X.
"""

ALL_INFO = collections.defaultdict(list)

def handle(generator: Iterator[int]) -> solver.ClueValueGenerator:
    def result(clue: Clue) -> Iterator[int]:
        def save_it(value: int, op: str) -> int:
            ALL_INFO[clue, str(value)].append(op)
            return value

        min_value, max_value = generators.get_min_max(clue)
        clue_number = clue.context
        for value in generator:
            if value >= clue_number * max_value:
                break
            if min_value <= (t := value + clue_number) < max_value:
                yield save_it(t, '+')
            if min_value <= (t := value - clue_number) < max_value:
                yield save_it(t, '-')
            if clue_number != 1:
                if min_value <= (t := value * clue_number) < max_value:
                    yield save_it(t, '*')
                t, r = divmod(value, clue_number)
                if r == 0:
                    yield save_it(t, '/')

    return result


def square()  -> Iterator[int]:
    return map(lambda x: x * x, itertools.count(1))

def cube() -> Iterator[int]:
    return map(lambda x: x * x * x, itertools.count(1))

def triangle() -> Iterator[int]:
    return map(lambda x: x * (x + 1) // 2, itertools.count(1))

def fibonacci() -> Iterator[int]:
    x = y = 1
    while True:
        yield y
        x, y = y, x + y

def sandp() -> Iterator[int]:
    for value in itertools.count(1):
        digits = [int(x) for x in str(value)]
        if 0 not in digits and value % sum(digits) == 0 and value % math.prod(digits) == 0:
            yield value

class Solver220(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver220()
        solver.verify_is_180_symmetric()
        solver.add_all_constraints()
        solver.solve(debug=0)

    def __init__(self) -> None:
        super().__init__(self.get_clue_list())
        self.A10 = self.clue_named("10a")

    def get_clue_list(self) -> Sequence[Clue]:
        grid_locations = [(-1, -1)] + Clues.get_locations_from_grid(GRID)

        across = ((1, 2, square),
                  (3, 2, triangle),
                  (4, 3, fibonacci),
                  (6, 3, cube),
                  (9, 2, triangle),
                  (10, 2, None))
        down = ((1, 3, cube),
                (2, 2, fibonacci),
                (3, 2, square),
                (5, 3, fibonacci),
                (7, 2, sandp),
                (8, 2, square))
        clues = [
            Clue(f'{number}{suffix}', is_across, grid_locations[number], length, generator=gen, context=number)
            for clue_list, is_across, suffix in ((across, True, 'a'), (down, False, 'd'))
            for number, length, generator in clue_list
            for gen in [handle(generator()) if generator else generators.allvalues]
        ]
        return clues

    def not_all_same(self, c1: Clue, c2: Clue, c3: Clue, c4: Clue) -> Any:
        def result(v1: ClueValue, v2: ClueValue, v3: ClueValue, v4: ClueValue) -> bool:
            temp1, temp2, temp3, temp4 = \
                ALL_INFO[c1, v1], ALL_INFO[c2, v2], ALL_INFO[c3, v3], ALL_INFO[c4, v4]
            if max(len(temp1), len(temp2), len(temp3), len(temp4)) > 1:
                return True
            if temp1[0] == temp2[0] == temp3[0] == temp4[0]:
                return False
            return True
        return result

    def add_all_constraints(self) -> None:
        clues = set(self._clue_list)
        clues.remove(self.A10)
        for four in itertools.combinations(clues, 4):
            self.add_constraint(four, self.not_all_same(*four))

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        locations = {location: int(letter)
                     for clue in self._clue_list
                     for location, letter in zip(clue.locations, known_clues[clue])}
        counter = collections.Counter()
        for clue, value in known_clues.items():
            if clue != self.A10:
                temp = ALL_INFO[clue, value]
                if len(temp) == 1:
                    counter[temp[0]] += 1

        assert len(locations) == 16
        total1 = sum(locations.values())
        total2 = locations[4, 3] * 10 + locations[4, 4]

        if counter['+'] <= 2 and total2 == total1 + 10:
            return True
        if counter['-'] <= 2 and total2 == total1 - 10:
            return True
        if counter['*'] <= 2 and total2 == total1 * 10:
            return True
        if counter['/'] <= 2 and total2 == total1 / 10:
            return True
        return False

    def show_solution(self, known_clues: KnownClueDict) -> None:
        print('============')
        for clue, value in known_clues.items():
            if clue != self.A10:
                print(clue.name, ALL_INFO[clue, value])
        locations = {location: int(letter)
                     for clue in self._clue_list
                     for location, letter in zip(clue.locations, known_clues[clue])}
        total1 = sum(locations.values())
        total2 = locations[4, 3] * 10 + locations[4, 4]
        print(total1, total2)
        super().show_solution(known_clues)


if __name__ == '__main__':
    Solver220.run()
