import itertools
import math
from collections.abc import Sequence, Iterator

from solver import ConstraintSolver, Clues, Clue, KnownClueDict

GRID = """
XXX.X
X..X.
X....
..X..
X..X.
"""


class Property:
    @staticmethod
    def generator():
        total = 0
        for i in itertools.count(1):
            total += i
            yield total

    @classmethod
    def within_bounds(cls, low, high) -> Iterator[int]:
        for value in cls.generator():
            if value < low:
                continue
            if value >= high:
                break
            yield value

    @classmethod
    def with_length(cls, length) -> Iterator[int]:
        return cls.within_bounds(10 ** (length - 1), 10 ** length)

    def __init__(self) -> None:
        self.items = set(self.within_bounds(10, 100_000))

    def __contains__(self, item: int) -> bool:
        return item in self.items


def digits(value: int) -> list[int]:
    return [int(x) for x in str(value)]


PROPERTY = Property()


def handle1a(clue: Clue) -> Iterator[int]:
    return (value for value in PROPERTY.with_length(clue.length)
            if math.prod(digits(value)) == 18)


def handle3a(clue: Clue) -> Iterator[int]:
    return (value for value in PROPERTY.with_length(clue.length)
            if math.prod(digits(value)) in PROPERTY)


def handle5a(_clue: Clue) -> Iterator[int]:
    generator = PROPERTY.generator()
    return itertools.islice(generator, 26, 27)


def handle7a(clue: Clue) -> Iterator[int]:
    return PROPERTY.with_length(clue.length)


def handle8a(clue: Clue) -> Iterator[int]:
    generator = PROPERTY.with_length(clue.length)
    return itertools.islice(generator, 1)


def handle9a(clue: Clue) -> Iterator[int]:
    return (value for value in PROPERTY.with_length(clue.length)
            if sum(digits(value)) == 19
            if str(value) == str(value)[::-1])


def handle10a(clue: Clue) -> Iterator[int]:
    return (value for value in PROPERTY.with_length(clue.length)
            for d in [digits(value)]
            if sum(d) > math.prod(d))


def handle2d(_clue: Clue) -> Iterator[int]:
    triangles = [x * (x + 1) // 2 for x in range(1, 150)]
    temp1 = {x + y for x, y in itertools.combinations_with_replacement(triangles, 2)}
    temp2 = [x for x in temp1 if 1000 <= x <= 9999 and x in PROPERTY]
    return sorted(temp2)


def handle3d(clue: Clue) -> Iterator[int]:
    for value in PROPERTY.with_length(clue.length):
        tens, ones = divmod(value, 10)
        if tens < ones:
            yield value


def handle4d(clue: Clue) -> Iterator[int]:
    for value in PROPERTY.with_length(clue.length):
        if math.prod(digits(value)) in PROPERTY:
            if (value2 := int(str(value)[::-1])) in PROPERTY and value2 != value:
                yield value


def handle6d(clue: Clue) -> Iterator[int]:
    for value in PROPERTY.with_length(clue.length):
        d = digits(value)
        if math.prod(d) == 0 and sum(d) in (1, 4, 9, 16, 25, 36, 49, 64):
            yield value


def handle7d(clue: Clue) -> Iterator[int]:
    for value in PROPERTY.with_length(clue.length):
        d = digits(value)
        if math.prod(d) % 15 == 0:
            a, b, c = d
            value1 = 100 * b + 10 * c + a
            value2 = 100 * c + 10 * a + b
            if any(x != value and x in PROPERTY for x in (value1, value2)):
                yield value


def handle8d(clue: Clue) -> Iterator[int]:
    yield from handle3d(clue)


class Solver221(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver221()
        solver.verify_is_180_symmetric()
        solver.add_all_constraints()
        solver.show_solution({})
        solver.solve(debug=True)

    def __init__(self) -> None:
        clues = self.get_clue_list()
        super().__init__(clues)
        self.a8 = self.clue_named("8a")

    @staticmethod
    def get_clue_list() -> Sequence[Clue]:
        grid_locations = [(-1, -1)] + list(Clues.get_locations_from_grid(GRID))

        across = ((1, 2, handle1a),
                  (3, 3, handle3a),
                  (5, 3, handle5a),
                  (7, 5, handle7a),
                  (8, 3, handle8a),
                  (9, 3, handle9a),
                  (10, 2, handle10a))
        down = ((2, 4, handle2d),
                (3, 2, handle3d),
                (4, 3, handle4d),
                (6, 4, handle6d),
                (7, 3, handle7d),
                (8, 2, handle8d))
        clues = [
            Clue(f'{number}{suffix}', is_across, grid_locations[number], length, generator=generator, context=number)
            for clue_list, is_across, suffix in ((across, True, 'a'), (down, False, 'd'))
            for number, length, generator in clue_list
        ]
        return clues

    def add_all_constraints(self) -> None:
        self.add_constraint(('3d', '8d'), lambda d3, d8: int(d3) > int(d8))

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        locations = {location: int(letter)
                     for clue in self._clue_list
                     for location, letter in zip(clue.locations, known_clues[clue])}
        actual_total = sum(locations.values())
        expected_total = int(known_clues[self.a8])
        return actual_total == expected_total


if __name__ == '__main__':
    Solver221.run()
