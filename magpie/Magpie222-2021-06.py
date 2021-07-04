import itertools
from typing import Sequence, Iterator, Callable, Any

from solver import Clue, generators, Clues, ConstraintSolver
from solver.constraint_solver import KnownClueDict


def digit_sum(number: int) -> int:
    return sum(int(x) for x in str(number))

def generate_if(generator, test: Callable[[str], bool]):
    def result(clue: Clue):
        return [x for x in generator(clue) if test(x)]
    return result

def generate_map(generator, mapper: Callable[[str], str]):
    def result(clue: Clue) -> Iterator[str]:
        return [mapper(x) for x in generator(clue)]
    return result

def generate_odd_digits(clue: Clue) -> Iterator[str]:
    return (''.join(digits) for digits in itertools.product('13579', repeat=clue.length))



GRID = """
X.XXXX
X..X..
XX.XX.
X.XX.X
X..X..
X.X.X.
"""

COLORS = """
123333
122344
111334
555644
575666
577776
"""

ACROSSES = [
    (1, 2, generators.square),
    (2, 2, generators.prime),
    (4, 2, generators.allvalues),
    (6, 3, generators.triangular),
    (7, 3, generators.known(123, 234, 345, 456, 567, 678, 789)),
    (8, 3, generators.square),
    (10, 3, generators.cube),
    (12, 3, generate_odd_digits),
    (14, 3, generators.allvalues),
    (16, 3, generators.triangular),
    (17, 3, generators.allvalues),
    (18, 2, generators.square),
    (19, 2, generators.not_prime),
    (20, 2, generators.square),
]

DOWNS = [
    (1, 3, generators.square),
    (2, 3, generators.palindrome),
    (3, 3, generators.square),
    (5, 3, generators.allvalues),
    (9, 2, generate_if(generators.allvalues, lambda x: int(x) % digit_sum(x) == 0)),
    (11, 2, generators.allvalues),
    (12, 3, generate_if(generators.prime, lambda x: str(x)[0] == str(x)[2])),
    (13, 3, generators.cube),
    (14, 3, generate_map(generators.triangular, lambda x : str(x)[::-1])),
    (15, 3, generators.triangular)
]

def is_anagram(a: str, b: str):
    a, b = str(a), str(b)
    return a != b and sorted(a) == sorted(b)


def is_multiple(a: str, b: str):
    a, b = int(a), int(b)
    return a != b and a % b == 0


from matplotlib import pyplot as plt


class Magpie221 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie221()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False, max_debug_depth=50)


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
                clue = Clue(f'{number}{letter}', is_across, grid[number - 1], length, generator=generator)
                clues.append(clue)
        return clues

    def add_all_constraints(self) -> None:
        self.add_constraint(('4a', '19a'), is_multiple)
        self.add_constraint(("6a", "14a"), is_multiple)
        self.add_constraint(("17a", "15d"), is_anagram)
        self.add_constraint(("2d", "18a"), is_multiple)
        self.add_constraint(("5d", "14a", "3d"), lambda d5, a14, d3: is_anagram(int(d5) - int(a14), d3))
        self.add_constraint(("11d", "9d", "19a"), lambda d11, d9, a19: int(d11) == int(d9) - int(a19))

    def show_solution(self, known_clues: KnownClueDict) -> None:
        foo = {location : int(digit)
               for clue, value in known_clues.items()
               for location, digit in zip(clue.locations, value)}
        if sum(foo.values()) == 126:
            super().show_solution(known_clues)


    def draw_grid(self, **args: Any) -> None:
        color_map = plt.rcParams['axes.prop_cycle'].by_key()['color']
        color_map = [x + '60' for x in color_map]
        colors = COLORS.strip().splitlines()
        shading = {(row + 1, col + 1): color_map[int(colors[row][col]) + 1]
                   for row in range(6)
                   for col in range(6)}
        args['shading'] = shading
        super().draw_grid(**args)

    def draw_grid(self, **args: Any) -> None:
        colors = COLORS.strip().splitlines()
        colors = {(row, column) : int(value)
                  for row, line in enumerate(colors, start=1)
                  for column, value in enumerate(line, start=1)}

        if True:
            args['location_to_clue_numbers'].clear()
            args['top_bars'] = {(row, column) for row in range(2, 7) for column in range(1, 7)
                                if colors[row, column] != colors.get((row - 1, column), None)
                                }
            args['left_bars'] = {(row, column) for row in range(1, 7) for column in range(2, 7)
                                 if colors[row, column] != colors.get((row, column - 1), None)
                                 }
        if False:
            clt = plt.cm.get_cmap('Set2', lut=7)
            color_map = [clt(i) for i in range(7)]

        color_map = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
                     'tab:brown', 'tab:pink',  'tab:gray', 'tab:olive', 'tab:cyan']

        color_map = [(207, 207, 207), # (95, 95, 95),  (0, 0, 0),
                     (163, 224, 72), (210, 59, 231), (235, 117, 50),
                     (230, 38, 31), (247, 208, 56), (126, 183, 248)]
        color_map = [(a / 256.0, b / 256.0, c / 256.0) for a, b, c in color_map]

        from random import shuffle
        shuffle(color_map)

        args['shading'] = {(row, col): color_map[colors[row, col] - 1]
                           for row in range(1, 7)
                           for col in range(1, 7)}

        super().draw_grid(**args)


if __name__ == '__main__':
    Magpie221.run()

