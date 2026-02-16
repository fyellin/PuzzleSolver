from collections.abc import Iterator, Sequence, Callable

import itertools
from collections import defaultdict
from itertools import product

from misc.UnionFind import UnionFind
from solver import Clue, ClueValue, Clues, ConstraintSolver

GRID = """
XX.XXXXX
X..X.X..
.XX.....
XX....X.
X..XX...
.XX...XX
X..XXX..
X...X..."""


def fibonacci_generator(max_val):
    i = j = 1
    while i < max_val:
        yield i
        i, j = j, i + j


SQUARES = {x * x for x in range(1, 1000)}
CUBES = {x * x * x for x in range(1, 100)}
TRIANGLES = {x * (x + 1) // 2 for x in range(2000)}
FIBONACCIS = set(fibonacci_generator(1_000_000))
SUM_OF_SQUARES = {x + y for x, y in itertools.combinations(SQUARES, 2) if x + y <= 10_000}

CLUES = [
    (1, 17,  4, lambda x: str(x) != str(x)[::-1]),   # not palindrome
    (5, 22,  3, lambda x: x in SQUARES),   # square
    (8, 2,   3, lambda x: True),    # multiple of 15
    (9, 15,  2, lambda x: x in TRIANGLES),   # triangular
    (10, 19, 3, lambda x: True),  # 2/3 of 23ac
    (11, 12, 5, lambda x: x in CUBES),  # cube of 16ac
    (13, 16, 4, lambda x: x in FIBONACCIS),  # fibonacci
    (15, 25, 2, lambda x: x in SQUARES),  # square
    (16, 3,  2, lambda x: x in FIBONACCIS),   # fibonacci
    (18, 7,  4, lambda x: True),   # same ds as 26
    (20, 10, 5, lambda x: x in TRIANGLES),  # triangle
    (23, 6,  3, lambda x: True),   # see above
    (24, 14, 2, lambda x: x % 2 == 0 and x // 2 in TRIANGLES),  # two times triangular
    (26, 21, 3, lambda x: True),  # see above
    (27, 1,  3, lambda x: x in SUM_OF_SQUARES),   # sum of two squares
    (28, 4,  4, lambda x: x in TRIANGLES),   # triangular number
]


def make_generator(predicate: Callable[[int], bool]) -> Callable[[Clue], Iterator[int]]:
    def generator(clue):
        for left in range(10 ** (clue.length - 1), 10 ** clue.length):
            if left % 10 == 0:
                continue
            if predicate(left + int(str(left)[::-1])):
                yield left
    return generator


class Listener4803(ConstraintSolver):
    @staticmethod
    def run(fancy=False) -> None:
        solver = Listener4803(fancy)
        solver.solve(debug=True)

    @staticmethod
    def run2(fancy=False) -> None:
        solver = Listener4803(fancy)
        solver.show_union_find()
        solver.print_arrows()

    def __init__(self, fancy) -> None:
        self.fancy = fancy
        clues = self.get_clues()
        super().__init__(clues)
        self.add_my_constraints()

    def get_clues(self):
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for (across, down, length, predicate) in CLUES:
            generator = make_generator(predicate)
            clues.append(Clue(f'{across}a', True, grid[across - 1], length,
                              generator=generator))
            clues.append(Clue(f'{down}d', False, grid[down - 1], length,
                              generator=generator))
        return clues

    def add_my_constraints(self):
        if not self.fancy:
            self.add_reversal_constraints()
        else:
            self.add_all_same_value_constraints()

        mapper = {left: right for left, right, _, _ in CLUES}

        def d_constraint(across1, across2, predicate):
            down1, down2 = mapper[across1], mapper[across2]
            self.add_constraint(f"{across1}a {down1}d {across2}a {down2}d",
                                lambda a1, d1, a2, d2:
                                    predicate(int(a1) + int(d1), int(a2) + int(d2)),
                                name=f"{across1}a-{across2}a")

        def digit_sum(x):
            return sum(int(c) for c in str(x))

        d_constraint(8,  15, lambda x, y: x % y == 0)
        d_constraint(10, 23, lambda x, y: y % 3 == 0 and x == y * 2 // 3)
        d_constraint(11, 16, lambda x, y: x == y ** 3)
        d_constraint(18, 26, lambda x, y: digit_sum(x) == digit_sum(y))

    def add_reversal_constraints(self):
        for across, down, _length, _predicate in CLUES:
            self.add_constraint(f"{across}a {down}d", lambda x, y: x == y[::-1],
                                name=f"{across}a-rev-{down}d")

    def add_all_same_value_constraints(self):
        location_to_id = {
            location: id for id, equivalence in enumerate(self.get_equivalences())
            for location in equivalence}

        id_to_clues = defaultdict(list)
        for clue in self._clue_list:
            for i, location in enumerate(clue.locations):
                id_to_clues[location_to_id[location]].append((location, clue, i))

        for common_spots in id_to_clues.values():
            for (location1, clue1, i1), (location2, clue2, i2) in (
                    itertools.combinations(common_spots, 2)):
                if location1 != location2:
                    self.add_constraint((clue1, clue2),
                                        lambda x, y, xi=i1, yi=i2: x[xi] == y[yi],
                                        name=f"{location1}={location2}")

    def get_equivalences(self, clues: Sequence[Clue] | None = None):
        clues = clues or self._clue_list
        uf = UnionFind[tuple[int, int]]()
        for (across, down) in itertools.batched(clues, 2):
            for location1, location2 in zip(across.locations, reversed(down.locations)):
                uf.union(location1, location2)
        result = defaultdict(set)
        for location in product(range(1, 9), repeat=2):
            result[uf.find(location)].add(location)
        return frozenset(frozenset(x) for x in result.values())

    def show_union_find(self):
        equivalences = sorted(self.get_equivalences(), key=min)
        loc_to_letter = {
            location: letter
            for locations, letter in zip(equivalences, "ABCDEFGHJKLMNPRSTUVWXYZ")
            for location in locations
        }
        clue_values = {clue: ClueValue(''.join(loc_to_letter[loc]
                                               for loc in clue.locations))
                       for clue in self._clue_list}
        self.plot_board(clue_values)

    def print_arrows(self):
        def show_arrows(plt, _axes):
            import matplotlib
            colors = matplotlib.colormaps['tab20b'].colors
            print(len(colors), len(CLUES))
            for (across, down, _, _), color in zip(CLUES, itertools.cycle(colors)):
                clue1, clue2 = [self.clue_named(x) for x in (f'{across}a', f'{down}d')]
                for (r1, c1), (r2, c2) in zip(clue1.locations, reversed(clue2.locations)):
                    if (r1, c1) == (r2, c2):
                        continue
                    if (r1, c1) in [(1, 8), (8, 1)]:
                        c1, c2 = c1 - .1, c2 - .1
                    plt.arrow(c1 + .5, r1 + .5, c2 - c1, r2 - r1, color=color, width=0.05)
        self.plot_board({}, extra=show_arrows)


if __name__ == '__main__':
    Listener4803.run(True)
