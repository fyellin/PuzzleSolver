import itertools
import math
from typing import Any, Iterator, Sequence, Union

from misc.factors import prime_factors
from solver import Clue, ClueValue, Clues, ConstraintSolver, DancingLinks, generators


def digit_sum(number: int) -> int:
    return sum(int(x) for x in str(number))


def generate_power(clue: Clue) -> Iterator[int]:
    minimum, maximum = generators.get_min_max(clue)
    for i in itertools.count(2):
        if i ** 3 >= maximum:
            break
        for power in itertools.count(3):
            value = i ** power
            if value >= maximum:
                break
            if value >= minimum:
                yield value


DICE = frozenset(("1", "2", "3", "4", "5", "6"))


def is_dice(value: ClueValue) -> bool:
    return all(x in DICE for x in str(value))


def is_multiple(big: ClueValue, little: ClueValue):
    q, r = divmod(int(big), int(little))
    return r == 0 and q > 1


def is_product_of_three_distinct_primes(value: ClueValue):
    factors = prime_factors(int(value))
    return len(factors) == 3 and all(count == 1 for _, count in factors)


TRIANGULARS = {i * (i + 1) // 2 for i in range(1000)}


def is_triangular(x: Union[int, ClueValue]) -> bool:
    return int(x) in TRIANGULARS


def is_square(x: Union[int, ClueValue]) -> bool:
    x = int(x)
    if x < 0:
        return False
    y = math.isqrt(x)
    return y * y == x


def generate_24a(clue: Clue):
    return generators.within_clue_limits(clue, (i ** 2 + (i + 1) ** 2 for i in itertools.count(2)))


GRID = """
XXX.XXXX
..XX....
X.XXX.XX
X...X...
X....XX.
.XXX.X..
XX...X.X
X.X..X..
X.X..X..
X...X...
"""

ACROSSES = [
    (1, 4, generators.prime),
    (4, 4, generate_power),
    (8, 4, None),
    (10, 3, None),
    (12, 3, generators.square),
    (14, 2, generators.triangular),
    (16, 3, None),
    (17, 4, None),
    (18, 5, generators.triangular),
    (19, 2, None),
    (21, 2, generate_power),
    (23, 5, None),
    (25, 4, generators.prime),
    (27, 3, None),
    (29, 2, None),
    (30, 3, None),
    (31, 3, None),
    (33, 4, None),
    (35, 4, generators.triangular),
    (36, 4, None),
]

DOWNS = [
    (1, 4, generators.square),
    (2, 6, generators.square),
    (3, 2, None),
    (5, 5, None),
    (6, 4, None),
    (7, 2, generate_power),
    (9, 7, generators.triangular),
    (11, 3, None),
    (13, 7, generators.square),
    (15, 4, generators.square),
    (18, 4, generate_power),
    (20, 6, generators.square),
    (22, 5, None),
    (24, 3, generate_24a),
    (26, 4, None),
    (28, 4, generators.square),
    (32, 2, None),
    (34, 2, generators.prime)
]


class Solver4686 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Solver4686()
        solver.plot_board()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)
        self.add_all_constraints()

    @staticmethod
    def get_clues() -> Sequence[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length, generator in information:
                clue = Clue(f'{number}{letter}', is_across, grid[number - 1], length,
                            generator=generator or generators.allvalues)
                clues.append(clue)
        return clues

    def add_all_constraints(self):
        def sum_is_triangular(x: ClueValue, y: ClueValue):
            return is_triangular(int(x) + int(y))

        def sum_is_square(x: ClueValue, y: ClueValue):
            return is_square(int(x) + int(y))

        def is_anagram(x: ClueValue, y: ClueValue):
            return sorted(x) == sorted(y)

        for clue in self._clue_list:
            self.add_constraint((clue,), is_dice)
        self.add_constraint(("8a", "18a"), sum_is_triangular)
        self.add_constraint(("10a", "34d"), is_multiple)
        self.add_constraint(("12a",), lambda x: int(x) % 2 == 0)
        self.add_constraint(("16a", "31a"), sum_is_triangular)
        self.add_constraint(("17a", "7d"), is_multiple)
        self.add_constraint(("19a",  "29a"), sum_is_triangular)
        self.add_constraint(("23a", "32d"), is_multiple)
        self.add_constraint(("27a", "16a"), sum_is_square)
        self.add_constraint(("29a",), lambda x: int(x) % 8 == 0 or int(x) % 27 == 0 and int(x) != 27)
        self.add_constraint(("30a", "24d"), lambda x, y: is_square(int(x) - int(y)))
        self.add_constraint(("31a", "16a"), sum_is_square)
        self.add_constraint(("33a", "30a"), is_multiple)
        self.add_constraint(("36a", "1d"), is_anagram)

        self.add_constraint(("3d",), is_product_of_three_distinct_primes)
        self.add_constraint(("5d",), is_product_of_three_distinct_primes)
        self.add_constraint(("6d", "7d", "18d"), lambda x, y, z: int(x) == int(y) + int(z))
        self.add_constraint(("11d",), lambda x: int(x) % 2 == 0 and is_square(int(x) // 2))
        self.add_constraint(("22d", "32d"), lambda x, y: is_multiple(x, int(y) ** 2))
        self.add_constraint(("26d",), lambda x: is_triangular(2 * int(x)))
        self.add_constraint(("32d", "19a", "7d"), lambda x, y, z: int(x) == int(y) - int(z))

    COLORS = ('#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6',
              '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3',
              '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#000000')

    def draw_grid(self, location_to_entry, top_bars, left_bars, **args: Any) -> None:
        if location_to_entry:
            solution = Part2(location_to_entry, top_bars=top_bars, left_bars=left_bars).solve()
            shading = {square: color for row, color in zip(solution, self.COLORS) for square in row}
        else:
            shading = {}
        super().draw_grid(location_to_entry=location_to_entry, top_bars=top_bars, left_bars=left_bars,
                          shading=shading, **args)


Shape = tuple[tuple[int, int], ...]


class Part2:
    def __init__(self, location_to_entry, top_bars, left_bars):
        self.top_bars = top_bars
        self.left_bars = left_bars
        self.grid = {location: int(value) for location, value in location_to_entry.items()}

    def handle_shape(self, shape: Shape):
        assert len(shape) == 6
        assert min(x for x, _ in shape) == 0
        assert min(x for _, x in shape) == 0

        seen = set()
        result = []

        for _ in range(2):
            for _ in range(4):
                if frozenset(shape) not in seen:
                    seen.add(frozenset(shape))
                    result.extend(self.hunt_for(shape))
                shape = self.rotate_right(shape)
            shape = self.mirror(shape)
        return result

    def hunt_for(self, shape: Shape):
        shape_set = set(shape)
        max_r = max(x for x, _ in shape)
        max_c = max(x for _, x in shape)
        for dr in range(1, 11 - max_r):
            for dc in range(1, 9 - max_c):
                values = [self.grid[r + dr, c + dc] for r, c in shape]
                if values[0] != values[1] and values[1] != values[2] and values[0] != values[2]:
                    if values[0] + values[3] == values[1] + values[4] == values[2] + values[5] == 7:
                        if not any((r + dr, c + dc) in shape_set and (r + dr - 1, c + dc) in shape_set
                                   for r, c in self.left_bars):
                            if not any((r + dr, c + dc) in shape_set and (r + dr, c + dc - 1) in shape_set
                                       for r, c in self.top_bars):
                                result = tuple((r + dr, c + dc) for r, c in shape)
                                yield result

    def rotate_right(self, shape: Shape) -> Shape:
        return self.normalize(tuple((y, -x) for x, y in shape))

    def mirror(self, shape: Shape) -> Shape:
        return self.normalize(tuple((x, -y) for x, y in shape))

    def normalize(self, shape: Shape) -> Shape:
        min_r = min(x for x, _ in shape)
        min_c = min(x for _, x in shape)
        return tuple((x - min_r, y - min_c) for x, y in shape)


    def solve(self):
        counter = 0
        constraints = {}
        results = []

        def doit(shape: Shape):
            nonlocal counter
            counter += 1
            constraint_name = f"Constraint{counter}"
            for result in self.handle_shape(shape):
                constraints[result] = [constraint_name]
                constraints[result].extend(f"R{r}C{c}" for r, c in result)

        doit(((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)))
        for (top, bottom) in ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1), (1, 2)):
            doit(((0, top), (1, 0), (1, 1), (2, bottom), (1, 2), (1, 3)))
        doit(((0, 0), (0, 1), (1, 2), (0, 2), (1, 3), (1, 4)))
        for bottom in (1, 2, 3):
            doit(((0, 0), (0, 1), (1, 1), (1, 2), (2, bottom), (1, 3)))

        optional_constraints = {f"R{r}C{c}" for r in range(1, 11) for c in range(1, 9)}
        dl = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=lambda x: results.append(x))
        dl.solve(debug=100)
        return results[0]

if __name__ == '__main__':
    Solver4686().run()
    #  PartSecond.run()
    # temp = Solver6220()
    # clue = temp.clue_named("15a")
    # result = list(x.code for x in clue.generator(clue))
    # print(result)

