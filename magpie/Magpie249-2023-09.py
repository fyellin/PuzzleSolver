import math
from collections import defaultdict
from collections.abc import Sequence
from itertools import combinations, pairwise
from math import isqrt

from misc import PRIMES
from solver import Clue, Clues, ConstraintSolver, EquationSolver, generators, KnownClueDict

GRID = """
X.XXX.X
XX.X.X.
..X....
X...X.X
XX.X...
X.X..X.
X..X....
"""

ACROSSES = [
    (1, 4), (4, 3), (6, 2), (8, 4), (10, 4), (11, 3), (12, 3), (15, 4), (17, 4), (19, 2),
    (20, 3), (21, 4)
]

DOWNS = [
    (1, 4), (2, 4), (3, 3), (4, 2), (5, 3), (7, 5), (9, 5), (12, 4), (13, 4), (14, 3),
    (16, 3), (18, 2)
]


class Magpie249 (ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie249()
        solver.solve(debug=True)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)
        for (clue1, clue2) in combinations(clues, 2):
            if clue1.length == clue2.length == 3:
                self.add_constraint((clue1, clue2), lambda x, y:
                                    not ('448' < x < '829' and '448' < y < '829'))

    def get_clues(self) -> Sequence[Clue]:
        all_values = generate_map().keys()
        """
         A=18 B=61 C=63 D=94 
         E=196, F=234, G=265, H=414, I=448, J=?, K=829, L=844  // 
         M=1098, P=2916, S=5239 // 
         W=17442 X=84636
        """
        my_generators = {
            2: generators.known(18, 61, 63, 94),
            5: generators.known(17442, 84636),
            4: generators.known(*(x for x in all_values if len(x) == 4 and x >= '1098')),
            3: generators.known(196, 234, 265, 414, 448, 829, 844,
                                *(x for x in all_values
                                  if len(x) == 3 and '448' < x < '829'))}
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length in information:
                clue_name = f'{number}{letter}'
                location = grid[number - 1]
                clue = Clue(clue_name, is_across, location, length,
                            generator=my_generators[length])
                clues.append(clue)
        return clues

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        m, n, o, p, q, r, s, t, u, v = sorted(
            int(x) for x in known_clues.values() if len(x) == 4)
        return p == 2916 and s == 5239

CLUES = [
    "A",
    "B",   # prime
    "E",   # square
    "F",   # multiple of A
    "G",   # from two distinct original square
    "H",   # ditto
    "I = A + E + F",
    "L = H + I - A",
    "M",   # product of two grid entries
    "P",   # square
    "S = 6K + G",
    "W = A(4F + D – B)",
    "X = DL + S + B",
]
class Magpie239b(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self):
        self.mapper = generate_map()
        clues = self.get_clues()
        super().__init__(clues, items=(int(x) for x in self.mapper))
        self.add_constraint(["B"], lambda x: is_prime(int(x)))
        self.add_constraint(["E"], lambda x: math.isqrt(int(x)) ** 2 == int(x))
        self.add_constraint(["F", "A"], lambda x, y: int(x) % int(y) == 0)

    def get_clues(self):
        clues = []
        for index, expression in enumerate(CLUES, start=1):
            name = CLUES[0]
            length = 2 if name <= "D" else 3 if name <= "L" else 4 if name <="V" else 5
            clue = Clue(name, True, (index, 1), length, expression=expression)
            clues.append(clue)
        return clues

def is_prime(x: int) -> bool:
    return x in PRIMES

def generate_map():
    result = defaultdict(list)
    for i in range(4, 317):
        square = str(i * i)
        for j, (c1, c2) in enumerate(pairwise(square)):
            if c1 != c2:
                if not (j == 0 and c2 == '0'):
                    reversal = square[:j] + c2 + c1 + square[j + 2:]
                    result[reversal].append(square)
    return result

def print_values():
    mapper = generate_map()
    for value in sorted(mapper.keys(), key=int):
        print(value, end='')
        if isqrt(int(value)) ** 2 == int(value) and len(value) <= 4:
            print('*', end='')
        if len(mapper[value]) >= 2 and len(value) <= 4:
            print(f'[{len(mapper[value])}]', end='')
        print(' ', end='')


def find_m():
    mapper = generate_map()
    for value1, value2 in combinations((x for x in mapper.keys() if len(x) <= 3), 2):
        value3 = str(int(value1) * int(value2))
        if len(value3) == 4 and value3 in mapper:
            print(value1, value2, value3)


def find_w():
    a, b, _c, d = 18, 61, 63, 94
    mapper = generate_map()
    for e in (169, 196):
        for f in (int(x) for x in mapper.keys() if len(x) == 3):
            i = a + e + f
            w = a * (4 * f + d - b)
            if 10000 <= w <= 99999 and str(w) in mapper:
                if 100 <= i <= 999 and str(i) in mapper:
                    print(e, f, i, w)


def find_x():
    b, d, l = 61, 94, 844
    mapper = generate_map()
    for s in (int(x) for x in mapper.keys() if len(x) == 4):
        x = d * l + s + b
        if 10000 <= x <= 99999 and str(x) in mapper:
            print(s, x)


if __name__ == '__main__':
    Magpie249.run()
