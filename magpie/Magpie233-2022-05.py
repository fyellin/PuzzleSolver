from __future__ import annotations

import itertools
from collections import Counter
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any, Unpack

from solver import Clue, ClueValue, Clues, ConstraintSolver, DancingLinks, DrawGridArgs, \
    Location, \
    generators, LetterCountHandler

GRID = """
XX.XXXXX
.XX..X..
X..X.X.X
XX...XX.
X....X.X
XX.XX.X.
XXX.X..X
X.X..X..
"""


def get_counts():
    counter = Counter()
    for i, j in itertools.combinations_with_replacement(range(1, 10), 2):
        if i + j not in {2, 3, 5, 7, 11, 13, 17}:
            counter[i] += 1
            counter[j] += 1
    result = [counter[i] for i in range(0, 10)]
    return result


def reverse_square(clue: Clue) -> Iterator[int]:
    for x in generators.square(clue):
        yield int(str(x)[::-1])


def reverse_prime(clue: Clue) -> Iterator[int]:
    for x in generators.prime(clue):
        yield int(str(x)[::-1])


ACROSSES = (
    (1, 3, generators.prime),
    (3, 3, generators.triangular),
    (6, 2, generators.prime),
    (8, 3, reverse_prime),
    (10, 2, generators.triangular),
    (12, 2, generators.allvalues),  # 2d is multiple of 12a
    (13, 3, generators.square),
    (15, 3, generators.square),
    (17, 3, generators.square),
    (19, 3, generators.prime),
    (20, 3, generators.prime),
    (22, 3, generators.prime),
    (24, 2, generators.allvalues),  # 24a = 32a + 18d
    (28, 2, generators.triangular),
    (30, 3, generators.allvalues),  # permutation of 13a
    (32, 2, generators.fibonacci),
    (33, 3, generators.triangular),
    (34, 3, generators.allvalues),  # permutation of 1a
)


DOWNS = (
    (1, 2, generators.triangular),
    (2, 3, generators.allvalues),  # multiple of 12a
    (3, 3, generators.square),
    (4, 3, generators.square),
    (5, 2, generators.fibonacci),
    (6, 3, generators.allvalues),  # multiple of reverse of 10a
    (7, 2, generators.square),
    (9, 3, generators.square),
    (11, 2, generators.triangular),
    (14, 2, generators.cube),
    (16, 2, generators.triangular),
    (18, 2, generators.allvalues),  # see 24a
    (19, 2, generators.cube),
    (20, 3, generators.triangular),
    (21, 2, generators.triangular),
    (23, 3, generators.cube),
    (24, 3, reverse_square),
    (25, 3, reverse_square),
    (26, 3, generators.palindrome),  # and also multiple of 5d
    (27, 2, generators.square),
    (29, 2, generators.allvalues),   # reverse of 11d
    (31, 2, generators.triangular)
)


def is_proper_multiple(x, y):
    x, y = int(x), int(y)
    return y > x and y % x == 0


def is_permutation(x, y):
    return x != y and sorted(x) == sorted(y)


CONSTRAINTS = [
    (('12a', '2d'), is_proper_multiple),
    (('24a', '32a', '18d'), lambda x, y, z: int(x) == int(y) + int(z)),
    (('30a', '13a'), is_permutation),
    (('34a', '1a'), is_permutation),

    (('10a', '6d'), lambda x, y: is_proper_multiple(x[::-1], y)),
    (('5d', '26d'), is_proper_multiple),
    (('29d', '11d'), lambda x, y: x == y[::-1]),
]


class Magpie233 (ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie233()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True, max_debug_depth=8)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, allow_duplicates=False,
                         # letter_handler=self.MyLetterCountHandler()
                         )
        self.add_puzzle_constraints()

    def get_clues(self) -> Sequence[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            for number, length, generator in information:
                clue = Clue(f'{number}{"a" if is_across else "d"}', is_across,
                            grid[number - 1], length, generator=generator)
                clues.append(clue)
        return clues

    def add_puzzle_constraints(self):
        for clues, expression in CONSTRAINTS:
            self.add_constraint(clues, expression)

    def get_allowed_regexp(self, location: Location) -> str:
        return '[^0]'

    class MyLetterCountHandler(LetterCountHandler):
        def start(self):
            super().start()
            counts = get_counts()
            for i in range(10):
                self._counter[chr(48 + i)] = -counts[i]

        def close(self):
            counts = get_counts()
            for i in range(10):
                assert self._counter[chr(48 + i)] == -counts[i]

        def real_checking_value(self, value: ClueValue, _info: Any) -> bool:
            counter = self._counter
            assert counter['0'] == 0
            result = all(value <= 0 for value in counter.values())
            return result

        @staticmethod
        def get_counts():
            counter = Counter()
            for i, j in itertools.combinations_with_replacement(range(1, 10), 2):
                if i + j not in {2, 3, 5, 7, 11, 13, 17}:
                    counter[i] += 1
                    counter[j] += 1
            result = [counter[i] for i in range(0, 10)]
            return result

    def draw_image(self, _plt, axes):
        from matplotlib.offsetbox import OffsetImage, AnnotationBbox
        from matplotlib.patches import Rectangle
        from PIL import Image

        rect = Rectangle((4, 4), 2, 2, linewidth=1, edgecolor='black', facecolor='gray')
        axes.add_patch(rect)

        filename = Path(__file__).parent / '..' / "misc" / "piemag.png"
        image = Image.open(filename)
        image.load()
        image_box = OffsetImage(image, zoom=1.5)
        ab = AnnotationBbox(image_box, (5, 5), frameon=False)
        axes.add_artist(ab)


    def draw_grid(self, **args: Unpack[DrawGridArgs]) -> None:
        super().draw_grid(**args, blacken_unused=False)
        return
        location_to_entry = args['location_to_entry']
        clued_locations = args['clued_locations']
        # self.get_words(clued_locations, location_to_entry)
        solution = self.solve_grid_entry(clued_locations, location_to_entry)
        top_bars = set()
        left_bars = set()
        for ((r1, c1), (r2, c2)) in solution:
            if r1 == r2:
                left_bars |= {(r1, c1), (r1, c1 + 2)}
                top_bars |= {(r1, c1), (r1, c1 + 1), (r1 + 1, c1), (r1 + 1, c1 + 1)}
            else:
                top_bars |= {(r1, c1), (r1 + 2, c1)}
                left_bars |= {(r1, c1), (r1, c1 + 1), (r1 + 1, c1), (r1 + 1, c1 + 1)}

        xargs = dict(top_bars=top_bars, left_bars=left_bars,
                     blacken_unused=False, subtext="MAGPIE",
                     location_to_clue_numbers={},
                     extra=self.draw_image)
        super().draw_grid(**(args | xargs))

    def solve_grid_entry(self, clued_locations, location_to_entry):
        primes = {2, 3, 5, 7, 11, 13, 17, 19}
        constraints = {}
        for loc1 in clued_locations:
            row, column = loc1
            val1 = location_to_entry[loc1]
            for loc2 in [(row, column + 1), (row + 1, column)]:
                if loc2 in clued_locations:
                    val2 = location_to_entry[loc2]
                    if int(val1) + int(val2) not in primes:
                        domino = min(val1, val2) + max(val1, val2)
                        constraints[loc1, loc2] = [str(loc1), str(loc2), domino]
        solutions = []
        links = DancingLinks(constraints, row_printer=lambda x: solutions.append(x))
        links.solve(debug=False)
        assert len(solutions) == 1
        return solutions[0]

    def get_words(self, clued_locations, location_to_entry):
        rows = []
        columns = []
        for rc in range(1, 9):
            rows.append(''.join(location_to_entry[rc, i] for i in range(1, 9)
                                if (rc, i) in clued_locations))
            columns.append(''.join(location_to_entry[i, rc]
                                   for i in range(1, 9) if (i, rc) in clued_locations))

        mapping = {str(ord(letter) - 64): letter
                   for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'}

        def find_words(word, index):
            length = len(word)
            assert index <= length
            if index == length:
                yield ''
                return
            letter1 = mapping[word[index]]
            for result in find_words(word, index + 1):
                yield letter1 + result
            letter2 = mapping.get(word[index:index + 2]) if index <= length - 2 else None
            if letter2 is not None:
                for result in find_words(word, index + 2):
                    yield letter2 + result

        for row, word in enumerate(rows, start=1):
            print(row, word)
            for result in find_words(word, 0):
                print(result)

        for col, word in enumerate(columns, start=1):
            print(col, word)
            for result in find_words(word, 0):
                print(result)


if __name__ == '__main__':
    Magpie233.run()
