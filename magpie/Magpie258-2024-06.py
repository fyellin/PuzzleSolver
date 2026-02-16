import itertools
import math
from typing import Any
from collections.abc import Sequence

from solver import Clue, Clues, ConstraintSolver, generators

GRID = """
XXXXXXXX
..X.....
XX.XX.X.
X.X...X.
X.X..X.X
X...X...
XXX...X.
X...X...
"""


ACROSS_LENGTHS = ((1, 4), (5, 4), (9, 4), (10, 4), (13, 4), (15, 2), (16, 4), (17, 2),
                  (19, 4), (22, 4), (23, 4), (24, 2), (26, 4), (27, 2), (28, 4), (29, 4))

DOWN_LENGTHS = ((1, 4), (18, 4), (2, 2), (11, 4), (25, 2), (3, 4), (19, 4), (4, 2),
                (12, 4), (5, 2), (13, 4), (6, 4), (20, 4), (7, 2), (14, 4), (27, 2),
                (8, 4), (21, 4))

TARGETS = [4185, 1963, 1364, 4863, 3524, "27d", 3124, "7d",
           9153, 3896, 8653, "4d", 8463, "25d", 7923, 5617,
           5983, "5d", 5497, 1953, 9273, 2384, 6845, 9164, 7683,
           4573, 3649, 6392, 7568, 5281, 4672, 2569, 3592, 5976]

PAIRS = "4d/24a, 5d/2d, 7d/17a, 25d/27a, 27d/15a"


def evaluate(a, b=None, c=None, d=None):
    if b is c is d is None:
        a, b, c, d = [int(x) for x in str(a)]
    return sum(math.comb(d, n) * (a ** n) * (b ** (d - n)) * (c ** ((d - n) // 2))
               for n in range(d, -1, -2))


class Magpie258(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)

    def get_clues(self) -> Sequence[Clue]:
        assert len(TARGETS) == len(ACROSS_LENGTHS) + len(DOWN_LENGTHS)
        clues: list[Clue] = []
        locations = Clues.get_locations_from_grid(GRID)
        for clue_list in (ACROSS_LENGTHS, DOWN_LENGTHS):
            is_across = clue_list == ACROSS_LENGTHS
            for number, length in sorted(clue_list):
                clue = Clue(f'{number}{'a' if is_across else 'd'}', is_across,
                            locations[number - 1], length)
                clues.append(clue)
        clue_by_name = {clue.name: clue for clue in clues}
        targets_to_values = get_targets()
        for index, (clue, target) in enumerate(zip(clues, TARGETS)):
            if isinstance(target, str):
                target_clue = clue_by_name[target]
                target_clue_index = clues.index(target_clue)
                new_clue = Clue(target_clue.name, target_clue.is_across, None, 4,
                                locations=(*target_clue.locations, *clue.locations))
                # clues[index] = None
                clues[target_clue_index] = new_clue
            else:
                values = targets_to_values[target]
                assert values
                clue.generator = generators.known(*values)

        return [clue for clue in clues if clue is not None]

    def plot_board(self, clue_values=None, **more_args: Any) -> None:
        shaded_squares = set()
        for clue, value in (clue_values or {}).items():
            if int(value) in TARGETS:
                shaded_squares.update(clue.locations)

        shaded_squares |= {(4, 3), (4, 6)}
        shading = dict.fromkeys(shaded_squares, 'yellow')
        super().plot_board(clue_values, shading=shading, **more_args)

        count1 = count2 = 0
        for clue, target in zip(self._clue_list, TARGETS):
            if isinstance(target, str):
                continue
            value = int(clue_values[clue])
            if target == evaluate(value):
                count1 += 1
            if value == evaluate(target):
                count2 += 1
        print(count1, count2)


def get_targets():
    targets = [x for x in TARGETS if isinstance(x, int)]

    results = {target: [] for target in targets}

    for index, value in enumerate(targets):
        result = evaluate(value)
        if 1234 <= result <= 9876 and '0' not in (s := str(result)) and len(set(s)) == 4:
            results[value].append(result)
    for a, b, c, d in itertools.permutations(range(1, 10), 4):
        result = evaluate(a, b, c, d)
        if result in results:
            results[result].append(1000 * a + 100 * b + 10 * c + d)
    return results


if __name__ == '__main__':
    Magpie258().run()
