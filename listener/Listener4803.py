import itertools
import math
import string
from collections import defaultdict
from itertools import product
from typing import Any

from misc.UnionFind import UnionFind
from solver import Clue, Clues, ConstraintSolver


GRID = """
XX.XXXXX
X..X.X..
.XX.....
XX....X.
X..XX...
.XX...XX
X..XXX..
X...X..."""

def fibonacci_generator():
    i = j = 1
    while True:
        yield i
        i, j = j, i + j

SQUARES = {x * x for x in range(1, 1000)}
CUBES = {x * x * x for x in range(1, 100)}
TRIANGLES = {x * (x + 1) // 2 for x in range(2000)}
FIBONACCIS = set(itertools.takewhile(lambda x: x <= 1_000_000, fibonacci_generator()))
SUM_OF_SQUARES = {x + y for x, y in itertools.combinations(SQUARES, 2) if x + y <= 10_000}

CLUES = [
    (1, 17, 4,  lambda x: str(x) != str(x)[::-1]),   # not palindrome
    (5, 22, 3,  lambda x: x in SQUARES),   # square
    (8, 2, 3,   lambda x: True),    # multiple of 15
    (9, 15, 2,  lambda x: x in TRIANGLES),   # trianguar
    (10, 19, 3, lambda x: True),  # 2/3 of 23ac
    (11, 12, 5, lambda x: x in CUBES),  # cube of 16ac
    (13, 16, 4, lambda x: x in FIBONACCIS),  # fibonacci
    (15, 25, 2, lambda x: x in SQUARES),  # square
    (16, 3, 2,  lambda x: x in FIBONACCIS),   # fibonacci
    (18, 7, 4,  lambda x: True),   # same ds as 26
    (20, 10, 5, lambda x: x in TRIANGLES),  # triangle
    (23, 6, 3,  lambda x: True),   # see above
    (24, 14, 2, lambda x: x % 2 == 0 and x // 2 in TRIANGLES),  # two times triangular
    (26, 21, 3, lambda x: True),  # see above
    (27, 1, 3,  lambda x: x in SUM_OF_SQUARES),   # sum of two squares
    (28, 4, 4,  lambda x: x in TRIANGLES),   # triangular number
]

def make_gen(condition):
    def generator(clue):
        length = clue.length // 2
        for left in range(10 ** (length - 1), 10 ** length):
            if left % 10 == 0: continue
            right = int(str(left)[::-1])
            value = left + right
            if condition(value):
                yield left * (10 ** length) + right
    return generator


class Listener4803(ConstraintSolver):
    @staticmethod
    def run():
        solver = Listener4803()
        solver.solve(debug=True)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues)
        self.add_my_constraints()

    def get_clues(self, all=False):
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for (across, down, length, predicate) in CLUES:
            aclue = Clue(f'{across}a', True, grid[across - 1], length)
            dclue = Clue(f'{down}d', False, grid[down - 1], length)
            if all:
                clues.extend([aclue, dclue])
            else:
                clue = Clue(str(across), True, None, None,
                            locations=aclue.locations + dclue.locations,
                            context = (aclue.name, dclue.name),
                            generator=make_gen(predicate))
                clues.append(clue)
        return clues

    def plot_board(self, clue_values = None, **more_args: Any) -> None:
        alt_clues = self.get_clues(True)
        alt_solver = ConstraintSolver(alt_clues)
        alt_clue_values = {}
        for clue, value in clue_values.items():
            left_name, right_name = clue.context
            left, right = value[0:len(value) // 2], value[len(value) // 2:]
            alt_clue_values[alt_solver.clue_named(left_name)] = left
            alt_clue_values[alt_solver.clue_named(right_name)] = right
        alt_solver.plot_board(alt_clue_values)

    def add_my_constraints(self):
        def v(value):
            assert len(value) % 2 == 0
            left = int(str(value[0:len(value) // 2]))
            right = int(str(value[len(value) // 2:]))
            return left + right

        def digit_sum(x):
            return sum(int(c) for c in str(x))

        self.add_constraint(("8 15"), lambda x, y: v(x) % v(y) == 0)
        self.add_constraint(("10 23"), lambda x, y: v(y) % 3 == 0 and v(x) == v(y) * 2 // 3)
        self.add_constraint(("11 16"), lambda x, y: v(x) == v(y) ** 3)
        self.add_constraint(("18 26"), lambda x, y: digit_sum(v(x)) == digit_sum(v(y)))


class Listener4803_xx(ConstraintSolver):
    @staticmethod
    def run():
        solver = Listener4803_xx()
        solver.verify_is_180_symmetric()
        # solver.handle_union_find()
        solver.print_arrows()

    def __init__(self):
        clues = Listener4803().get_clues(True)
        super().__init__(clues)

    def print_arrows(self):
        arrows = [(location1, location2)
                  for across, down, _, _ in CLUES
                  for clue1, clue2 in [[self.clue_named(f'{across}a'), self.clue_named(f'{down}d')]]
                  for location1, location2 in zip(clue1.locations, reversed(clue2.locations))]
        def print_arrows(plt, axes):
            import matplotlib
            colors = matplotlib.colormaps['Set2'].colors
            print(len(colors), len(CLUES))
            for (across, down, _, _), color in zip(CLUES, itertools.cycle(colors)):
                clue1, clue2 = [self.clue_named(x) for x in (f'{across}a', f'{down}d')]
                for (r1, c1), (r2, c2) in zip(clue1.locations, reversed(clue2.locations)):
                    plt.arrow(c1 + .5, r1 + .5, c2 - c1, r2 - r1, color=color, width=0.05)
        self.plot_board({}, extra=print_arrows)


    def handle_union_find(self):
        uf = UnionFind[tuple[int, int]]()
        for (across, down, length, _) in CLUES:
            clue1 = self.clue_named(f'{across}a')
            clue2 = self.clue_named(f'{down}d')
            for location1, location2 in zip(clue1.locations, reversed(clue2.locations)):
                uf.union(location1, location2)
        letters = list("ABCDEFGHJKLMNPRSTUVWXYZ")
        tag_to_letter = {}
        letter_to_count = defaultdict(int)
        location_to_letter = {}
        for location in product(range(1, 9), repeat=2):
            tag = uf.find(location)
            if (letter := tag_to_letter.get(tag)) is None:
                letter = tag_to_letter[tag] = letters.pop(0)
            location_to_letter[location] = letter
            letter_to_count[letter] += 1
        self.plot_board({}, xyz=location_to_letter)
        for key, count in letter_to_count.items():
            print(key, count)

    def draw_grid(self, xyz=None, **args: Any) -> None:
        if xyz:
            args['location_to_entry'] = xyz
        super().draw_grid(**args)

def foobar():
    for x, y in itertools.combinations(range(1, 50), 2):
        if x ** 2 + y ** 2  == 1130:
            print(x, y)
if __name__ == '__main__':
   # Listener4803_xx.run()
   # fibo_test(2)  ## must be 55
   # fibo_test(4)  ## must be 6765
   # square_test(2)  ## must be 121   with I + O = 9
   # square_test(3)
   # cube(5)
   Listener4803.run()


