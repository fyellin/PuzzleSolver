import math
from typing import Any
from collections.abc import Sequence

import solver.generators as gen
from misc.Pentomino import Pentomino, PentominoSolver, get_graph_shading
from solver import Clue, Clues, Constraint, ConstraintSolver, KnownClueDict

GRID = """
X.XXXX
X.XX..
.X.XX.
X.XX.X
.XX.X.
X..X..
"""


def digit_product(x):
    return math.prod(int(ch) for ch in str(x))


def fibonacci():
    a, b = 0, 1
    while a < 1000:  # only generate numbers less than 1000000
        yield a
        a, b = b, a + b


FIBONACCI_SET = set(fibonacci())


SQUARE_SET = {x * x for x in range(0, 100)}


ACROSSES = [
    (1, 3, gen.square),
    (3, 3, gen.triangular),
    (6, 2, Constraint("6a 9a", lambda x, y: x == y[::-1])),
    (7, 2, Constraint("7a 9a", lambda x, y: int(x) == digit_product(y))),
    (9, 2, gen.allvalues),
    (10, 3, Constraint("10a 20a", lambda x, y: x != y and sorted(x) == sorted(y))),
    (12, 3, Constraint("10a 12a", lambda x, y: x == y[::-1])),
    (14, 2, gen.fibonacci),
    (17, 2, Constraint("17a", lambda x: int(x) % 2 == 1)),
    (18, 2, gen.triangular),
    (19, 3, gen.triangular),
    (20, 3, gen.square),
]

DOWNS = [
    (1, 3, gen.triangular),
    (2, 3, gen.triangular),
    (4, 2, Constraint("4d", lambda x: int(x[::-1]) in SQUARE_SET)),
    (5, 3, gen.square),
    (8, 2, Constraint("8d 7a", lambda x, y: int(x) + int(y) in FIBONACCI_SET)),
    (9, 2, gen.triangular),
    (11, 2, Constraint("11d 7a 13d", lambda x, y, z: int(x) == int(y) + int(z))),
    (12, 3, gen.square),
    (13, 2, gen.allvalues),
    (14, 3, gen.triangular),
    (15, 3, gen.triangular),
    (16, 2, Constraint("16d 4d", lambda x, y: int(x) == digit_product(y)))
]

TETRAMINOS = dict(
    I='XXXX', O="XX/XX", T="XXX/.X.", J="X/XXX", L="XXX/X", S=".XX/XX.", Z="XX/.XX",
    I2="XX", I3="XXX", L3="XX/X")

tetraminos = Pentomino.all_pentominos(TETRAMINOS, mirror=False)


class Magpie255 (ConstraintSolver):
    last_result: dict[str, tuple[tuple[int, int], ...]] | None

    @staticmethod
    def run():
        solver = Magpie255()
        solver.solve(debug=True)
        print(solver.count)

    def __init__(self) -> None:
        self.count = 0
        self.last_result = None
        clues, constraints = self.get_clues()
        super().__init__(clues, constraints)

    def get_clues(self) -> tuple[Sequence[Clue], Sequence[Constraint]]:
        clues = []
        constraints = []
        locations = Clues.get_locations_from_grid(GRID)
        for clue_list in (ACROSSES, DOWNS):
            is_across = clue_list == ACROSSES
            for number, length, other in clue_list:
                clue = Clue(f'{number}{'a' if is_across else 'd'}', is_across,
                            locations[number - 1], length)
                clues.append(clue)
                if isinstance(other, Constraint):
                    constraints.append(other)
                    clue.generator = gen.allvalues
                else:
                    clue.generator = other
        return clues, constraints

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        location_to_value = {location: int(value)
                             for clue, entry in known_clues.items()
                             for location, value in zip(clue.locations, entry)}
        total = sum(location_to_value.values())
        quotient, remainder = divmod(total, 10)
        if remainder != 0:
            return False

        def predicate(pixels):
            return all(pixel in location_to_value for pixel in pixels) and \
                   sum(location_to_value[pixel] for pixel in pixels) == quotient

        temp = ''.join(str(location_to_value[i, j]) for i in range(1, 7) for j in range(1, 7))
        print(temp)

        result = PentominoSolver().solve(6, 6, predicate,
                                         all_pentominos=tetraminos, debug=100)
        if result:
            self.last_result = result[0]
        return bool(result)

    def draw_grid(self, top_bars, left_bars, location_to_clue_numbers, **args: Any) -> None:
        shading = get_graph_shading(self.last_result)
        # left_bars, top_bars = get_hard_bars(self.last_result)
        super().draw_grid(shading=shading,
                          # top_bars=top_bars,
                          # left_bars=left_bars,
                          # location_to_clue_numbers=location_to_clue_numbers,
                          **args)



if __name__ == '__main__':
    Magpie255.run()
