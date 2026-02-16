from typing import Unpack

import math
from collections import defaultdict
from collections.abc import Sequence, Iterable
from functools import cache

from misc.Tester import FastDijkstra, State
from solver import Clue, Clues, ConstraintSolver, DrawGridArgs, generators, Constraint
from solver.generators import known, palindrome, prime, square

GRID = """
XX.XXXX
..XX.X.
X.X.X.X
.XX....
X..X.X.
X.X...X
X.X.X..
"""


def digit_sum(n):
    return sum(int(i) for i in n)


def digit_product(n):
    return math.prod(int(i) for i in n)


def is_permutation(a, b):
    return a != b and sorted(a) == sorted(b)


def is_square(x):
    return 0 <= x == math.isqrt(x) ** 2


def is_reverse(x, y):
    return x == y[::-1]


ACROSSES = [
    (1, 3, square, Constraint('1a 3a', lambda x, y: int(x) == int(y) ** 2)),
    (3, 2),
    (5, 2, square),
    (7, 3, Constraint('7a 1d', lambda x, y: int(x) % int(y) == 0)),
    (9, 2, Constraint('9a 10a', lambda x, y: int(x) == digit_product(y))),
    (10, 2, Constraint('10a 18a', is_reverse)),
    (11, 2, Constraint('11a 1d 9a', lambda x, y, z: int(x) == int(y) + int(z))),
    (12, 3, Constraint('12a 20d', lambda x, y: int(x) % int(y) == 0)),
    (15, 3, prime, Constraint('15a 12d', is_permutation)),
    (16, 3, Constraint('16a 12a', is_permutation)),
    (17, 2, prime),
    (18, 2),
    (19, 2, Constraint('19a 22a', lambda x, y: is_square(int(x) - int(y)))),
    (20, 3, palindrome),
    (22, 2, square),
    (23, 2, prime, Constraint('23a 11d 14d',
                              lambda x, y, z: (int(y) - int(z)) % int(x) == 0)),
    (24, 3, square, Constraint('24a 23a', lambda x, y: int(x) == int(y) ** 2))
]

DOWNS = [
    (1, 2),
    (2, 3, square, Constraint('2d 6d', lambda x, y: int(x) == int(y) ** 2)),
    (4, 2, Constraint('4d 19d', is_reverse)),
    (6, 2, prime, Constraint('6d 19a', lambda x, y: int(y) % int(x) == 0)),
    (8, 2, Constraint('8d 19a', lambda x, y: int(x) == digit_product(y))),
    (9, 3, palindrome),
    (10, 3, known(*[math.prod(range(i, i + j))
                    for i in range(1, 10) for j in range(2, 10)])),   # deal with this
    (11, 3, palindrome),
    (12, 3, prime, Constraint('12d', lambda x: x[0] < x[1] < x[2])),
    (13, 3, Constraint('13d 10d', is_reverse)),
    (14, 3, square),
    (17, 2, Constraint('17d 4d', lambda x, y: int(x) % int(y) == 0)),
    (18, 3, Constraint('18d 2d', lambda x, y: digit_sum(x) == digit_sum(y))),
    (19, 2, prime),
    (20, 2, palindrome),
    (21, 2, Constraint('21d', lambda x: is_square(int(x[::-1]))))
]


class Magpie245 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie245()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self) -> None:
        clues, constraints = self.get_clues()
        self.constraints = constraints
        super().__init__(clues, constraints=constraints,)

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

    def draw_grid(self, location_to_entry, **args: Unpack[DrawGridArgs]) -> None:
        paths = self.get_paths(location_to_entry)

        # import matplotlib
        # import colorsys
        # cmap = matplotlib.cm.get_cmap('tab10')
        # colors2 = [colorsys.hls_to_rgb(h, min(1, l * 1.5), s=s)
        #           for i in range(4)
        #           for r, g, b, alpha in [cmap(.25 * i)]
        #           for h, l, s in [colorsys.rgb_to_hls(r, g, b)]]
        # print(cmap(0))
        colors = ['pink', 'lightblue', 'lightgreen', 'yellow']
        shading = {location: color
                   for locations, color in zip(paths, colors)
                   for location in locations}
        letters = []
        for path in paths:
            first, last = location_to_entry[path[0]], location_to_entry[path[-1]]
            assert first == last
            total = sum(int(location_to_entry[location]) for location in path[1:-1])
            letter_index = (total - 1) % 26
            letter = chr(65 + letter_index)
            letters.append((first, letter))
        subtext = ''.join(letter for _, letter in sorted(letters))
        super().draw_grid(location_to_entry=location_to_entry, shading=shading,
                          subtext=subtext,
                          **args)

    def get_paths(self, location_to_entry):
        digit_to_locations = defaultdict(list)
        for location, value in location_to_entry.items():
            digit_to_locations[int(value)].append(location)
        doubles = sorted((values for key, values in digit_to_locations.items()
                          if len(values) == 2))
        starts = [start for (start, _) in doubles]
        ends = [end for (_, end) in doubles]
        solver = MyDijkstra(starts, ends)
        _distance, result = solver.run(verbose=3)
        return result


class MyDijkstra (FastDijkstra):
    @staticmethod
    def go():
        starts = ((1, 7), (2, 4), (1, 1), (2, 7))
        ends = ((7, 7), (7, 6), (6, 2), (5, 4))
        solver = MyDijkstra(starts, ends)
        return solver.run(verbose=0)

    def __init__(self, starts, ends):
        self.starts = tuple(starts)
        self.ends = tuple(ends)
        initial_state = tuple((x,) for x in self.starts)
        super().__init__(initial_state)

    def is_done(self, state: State) -> bool:
        return all(x[-1] == y for x, y in zip(state, self.ends))

    @staticmethod
    @cache
    def nearby(item):
        r, c = item
        return [(r + dr, c + dc)
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                if 1 <= r + dr <= 7 and 1 <= c + dc <= 7]

    def neighbor(self, state: State) -> Iterable[State]:
        def minimize(element):
            index, path = element
            return 1000 if path[-1] == self.ends[index] else len(path)

        index, path = min(enumerate(state), key=minimize)
        neighbors = self.nearby(path[-1])
        if self.ends[index] in neighbors:
            yield *state[0:index], (*path, self.ends[index]), *state[index + 1:]
            return

        used = set(x for path in state for x in path)
        used.update(self.ends)
        used.update(x for pt in path[:-1] for x in self.nearby(pt))

        for neighbor in neighbors:
            if neighbor not in used:
                yield *state[0:index], (*path, neighbor), *state[index + 1:]


if __name__ == '__main__':
    Magpie245.run()
    # MyDijkstra.go()
