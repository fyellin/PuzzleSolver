import itertools
from collections import defaultdict
from collections.abc import Iterable, Iterator, Sequence, Callable
from typing import Any

from solver import Clue, Clues, ClueValueGenerator, ClueValue, ConstraintSolver, Location, generators

GRID = """
.....XX.....
.XXXX..XX.X.
X.X..XX.XX.X
...XX.XX....
X.X....X.X..
............
"""

ROTATIONS = """
.....13
.1113333113
331103301133
3.21031232.3
22222..00202
..1.2..0.1
"""

SHADING = """
.....12
.3111122224.
333315624444
7.35556664.8
77775..68888
..7.5..6.8
"""

generators.BASE = 16

CUBES = {i ** 3 for i in range(1, 50) if i ** 3 <= 0xFFFF}

SQUARES = {i ** 2 for i in range(1, 0x100)}

TWO_CUBES_DELTA = {
    value for i in range(1, 0x100) for j in range(1, i) for value in [i*i*i - j*j*j] if value <= 0xFFFF
}

TWO_CUBES_SUM = {
    value for i in range(1, 0x100) for j in range(1, i) for value in [i*i*i + j*j*j] if value <= 0xFFFF
}

PRIMES = tuple(itertools.takewhile(lambda x: x < 0xFFF, generators.prime_generator()))


def ix(n: int) -> ClueValue:
    return ClueValue(hex(n)[2:])


def xi(s: str) -> int:
    return int(s, 16)


def digit_sum(value: ClueValue) -> int:
    return sum(xi(d) for d in value)


def max_prime_factor(value: int) -> int:
    return max(x for x in PRIMES if x <= value and value % x == 0)


# 4a: Sum of first four digits is a square; sum of last four digits is a square; digit sum is a palindrome
def handle_4a(_: Clue) -> Iterable[str]:
    sum_of_four: dict[int, list[str]] = defaultdict(list)
    for i, j, k, l in itertools.product(range(16), repeat=4):
        if i + j + k + l in SQUARES:
            sum_of_four[i + j + k + l].append(ix(i) + ix(j) + ix(k) + ix(l))
    result: list[str] = []
    for a in sorted(sum_of_four.keys()):
        for b in sorted(sum_of_four.keys()):
            if (a + b) % 17 == 0:
                for x, y in itertools.product(sum_of_four[a], sum_of_four[b]):
                    result.append(x + y)
    return result


# 15a: One prime factor is a two-digit palindrome; both the fi st and fourth digits are twice the second.
def handle_15a(_: Clue) -> Iterator[str]:
    for i in range(1, 8):
        for j in range(16):
            for k in range(16):
                temp = ((2 * i) << 16) + (i << 12) + (j << 8) + ((2 * i) << 4) + k
                if temp % 17 == 0:
                    yield ix(temp)


# Ea: One more than the sum of two even cubes; contains the same digit three times.
# noinspection PyPep8
def handle_Ea(_: Clue) -> Iterator[str]:
    # The sum of two even cubes is the same as 8 times the sum of two cubes
    for cube_sum in TWO_CUBES_SUM:
        value = ix(8 * cube_sum + 1)
        if len(value) == 4:
            if any(value.count(x) == 3 for x in value):
                yield value


# 7d Reverse of one more than twice a cube
def handle_7d(_: Clue) -> Iterable[str]:
    # Note that 10 is probably a little bit too much, but that's okay.  Wrong length values get filtered out
    return [ix(2 * i * i * i + 1)[::-1] for i in range(1, 10)]


def fixed(items: Iterable[int]) -> ClueValueGenerator:
    """Converts a list of items into a Clue"""
    def generator(clue: Clue) -> Iterable[str]:
        min_value, max_value = generators.get_min_max(clue)
        return [ix(item) for item in items if min_value <= item < max_value]
    return generator


def all_values(clue: Clue) -> Iterable[str]:
    min_value, max_value = generators.get_min_max(clue)
    return [ix(value) for value in range(min_value, max_value)]


def reverse_delta(delta: int) -> Callable[[ClueValue, ClueValue], bool]:
    return lambda x, y: x == ix(xi(y) + delta)[::-1]


ACROSS: Sequence[tuple[str, int, ClueValueGenerator | None]] = (
    ('4', 8, handle_4a),
    ('A', 4, None),
    # Ca: Twice a cube.
    ('C', 2, fixed(2 * x for x in CUBES)),
    ('E', 4, handle_Ea),
    ('11', 3, None),
    ('13', 3, None),
    ('15', 5, handle_15a),
    ('17', 5, None),
)

DOWN: Sequence[tuple[str, int, ClueValueGenerator | None]] = (
    # 1d: Has two cubed as a factor; ....
    ('1', 2, fixed(range(0x10, 0xFF, 8))),
    # 2d: Digit sum is a cube; largest prime factor is the difference between two cubes.
    ('2', 2, fixed(i for i in range(0x10, 0x100)
                   if digit_sum(ix(i)) in CUBES and max_prime_factor(i) in TWO_CUBES_DELTA)),
    ('3', 2, None),
    ('5', 2, None),
    ('6', 2, None),
    ('7', 2, handle_7d),
    # 8d: Has the number of faces on a cube as a factor; smallest answer in the puzzle
    ('8', 2, fixed(range(6, 0x100, 6))),
    ('9', 2, None),
    ('A', 3, None),
    # Bd: Difference between two cubes
    ('B', 2, fixed(TWO_CUBES_DELTA)),
    # Cd: Four less than a cube
    ('C', 2, fixed(x - 4 for x in CUBES)),
    # Dd: ... digit sum is a square
    ('D', 2, fixed(x for x in range(0x10, 0x100) if digit_sum(ix(x)) in SQUARES)),
    ('F', 2, None),
    ('10', 3, None),
    # 12d: Two less than the sum of two cubes:
    ('12', 3, fixed(x - 2 for x in TWO_CUBES_SUM)),
    ('14', 3, None),
    # 16d: Twice a cube
    ('16', 2, fixed(2 * x for x in CUBES)),
    ('18', 2, None)
)


def make_clue_list() -> Sequence[Clue]:
    locations = Clues.get_locations_from_grid(GRID)
    clues = []
    for (is_across, clue_info, suffix) in (True, ACROSS, 'a'), (False, DOWN, 'd'):
        for name, length, generator, in clue_info:
            generator = generator or all_values
            clue = Clue(name + suffix, is_across, locations[int(name, 16) - 1], length, generator=generator)
            clues.append(clue)
    return clues


class MySolver(ConstraintSolver):
    def __init__(self, clue_list: Sequence[Clue]) -> None:
        super().__init__(clue_list)

        # Aa: Difference between two cubes plus the difference between Cd and 8d
        self.add_constraint(('Aa', 'Cd', '8d'),
                            lambda x, y, z: xi(x) - (xi(y) - xi(z)) in TWO_CUBES_DELTA)  # this = TCD + (Cd - 8d)
        # 11a: Same digit sum as 13a
        self.add_constraint(('11a', '13a'), lambda x, y: digit_sum(x) == digit_sum(y))
        # 13a: Sum of 11a, 8d and Bd
        self.add_constraint(('13a', '11a', '8d', 'Bd'), lambda a, x, y, z: xi(a) == xi(x) + xi(y) + xi(z))
        # 17a: Bd cubed minus(a third of 8d) cubed minus 8d
        self.add_constraint(('17a', 'Bd', '8d'), lambda a, x, y: xi(a) == xi(x)**3 - (xi(y) // 3) ** 3 - xi(y))
        # 1d: ... has same largest prime factor as 7d
        self.add_constraint(('1d', '7d'), lambda x, y: max_prime_factor(xi(x)) == max_prime_factor(xi(y)))
        # 3d: Reverse of one more than 2d
        self.add_constraint(('3d', '2d'), reverse_delta(1))
        # 5d: Reverse of two more than Cd
        self.add_constraint(('5d', 'Cd'), reverse_delta(2))
        # 6d: 1d plus a cube
        self.add_constraint(('6d', '1d'), lambda x, y: xi(x) - xi(y) in CUBES)
        # 8d: ... smallest answer in the puzzle
        for clue in self._clue_list:
            if clue.name != '8d' and clue.length == 2:
                self.add_constraint(('8d', clue), lambda x, y: xi(x) < xi(y), name=f'8d < {clue.name}')
        # 9d: Sum of 8d and Fd
        self.add_constraint(('9d', '8d', 'Fd'), lambda x, y, z: xi(x) == xi(y) + xi(z))
        # Ad: Cube minus Ca minus Cd (3)
        self.add_constraint(('Ad', 'Ca', 'Cd'), lambda x, y, z: xi(x) + xi(y) + xi(z) in CUBES)
        # Dd: 8d plus a cube; ...
        self.add_constraint(('Dd', '8d'), lambda x, y: xi(x) - xi(y) in CUBES)
        # Fd: Reverse of one less than 16d
        self.add_constraint(('Fd', '16d'), reverse_delta(-1))
        # 10d: Sum of 3d, 6d, Ad and 16d
        self.add_constraint(('10d', '3d', '6d', 'Ad', '16d'),
                            lambda a, w, x, y, z: xi(a) == xi(w) + xi(x) + xi(y) + xi(z))
        # 14d: Sum of Ca, 5d, 9d and Ad
        self.add_constraint(('14d', 'Ca', '5d', '9d', 'Ad'),
                            lambda a, w, x, y, z: xi(a) == xi(w) + xi(x) + xi(y) + xi(z))
        # 18d: Difference between 9d and 7d
        self.add_constraint(('18d', '9d', '7d'), lambda x, y, z: xi(x) == xi(y) - xi(z))


    def draw_grid(self, **args: Any) -> None:

        args['location_to_clue_numbers'] = {clue.base_location: [clue.name[0:-1]] for clue in self._clue_list}
        super().draw_grid(**args)

        location_to_entry: dict[Location, str] = args['location_to_entry']
        location_to_entry = {location: 'BYGADMORPHICNETS'[int(value, 16)]
                             for location, value in location_to_entry.items()}
        args['location_to_entry'] = location_to_entry
        args['location_to_clue_numbers'].clear()

        rotations = {}
        for row, line in enumerate(ROTATIONS.strip().split()):
            for column, item in enumerate(line):
                if item != '.':
                    rotations[row+1, column + 1] = int(item) * 90

        shading = {(row, column): "white" for row in range(1, 7) for column in range(1, 13)}
        colormap = ["", '#D1E8B4', '#FBD3A5', '#FBF888', '#F5B1D0', '#F8BBA6', '#C9C6E3', '#C9C6E3', '#E1C698']
        for row, line in enumerate(SHADING.strip().split()):
            for column, item in enumerate(line):
                if item != '.':
                    shading[row+1, column + 1] = colormap[int(item)]

        super().draw_grid(rotations=rotations, shading=shading, **args)


def run() -> None:
    clue_list = make_clue_list()
    solver = MySolver(clue_list)
    solver.solve(debug=True)


if __name__ == '__main__':
    run()
