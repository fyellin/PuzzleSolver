import itertools
import time
from collections.abc import Sequence

from misc import PRIMES
from solver import Clues, EquationSolver, KnownClueDict, KnownLetterDict

GRID = """
X.XXXXXX
X.....X.
XX.X....
X..X...X
..X.....
X...XX..
X..X....
X...X...
"""

ACROSSES = """
1 (H + H)(H + H) -E + H (4)
5 CH-B-D (3)
8 AAA  (5)
9 B + B  (2)
10 BH + D-G (3)
12 BBB  (5)
13 (G + G)(B + G)(B + G) (6)
16 BH(H(B -H) + B) + H  (6)
17 CCC  (5)
19 A(A +G- F) (3)
20 E-C+ H (2)
21 DDD  (5)
22 B(D-A) + F - G  (3)
23 (H + H)(H+ H) + H  (4)
"""

DOWNS = """
1 EEE (5)
2 (C + E)(C-G) + E+ G (3)
3 G(B -H) (3)
4 FFF (5)
5 G(C-E)(D - B + H) (4)
6 (D + D)(D + E)(E + H) (6)
7 A (2)
11 (D + D)(D + H)(H + A)  (6)
14 GGG  (5)
15 HHH   (5)
16 BB + CF + H  (4)
18 (B + E)(B - E) + A + E  (3)
19 G(F -H) + B + F  (3)
20 B - E  (2)
"""


class Magpie260 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False)

    def __init__(self) -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSSES, DOWNS, grid)
        super().__init__(clues, items=range(100))

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        permutation = get_permutation(known_clues.values())
        print(known_letters)
        translation = str.maketrans("0123456789", ''.join(permutation))
        known_clues2 = {clue: value.translate(translation) for clue, value in known_clues.items()}
        super().show_solution(known_clues, known_letters)
        super().show_solution(known_clues2, known_letters)


VALUES = tuple(str(x) for x in [50653, 74, 34, 39304, 74088, 13824, 851, 13, 221184,
                                19683, 646, 405, 1934, 298760, 10648, 1958, 619, 85184,
                                275264, 831, 325248, 385, 331, 14, 623, 6264, 32768, 2735])

PRIME_SET = {tuple(str(x)) for x in PRIMES}


def get_permutation(values: Sequence[str] = VALUES):
    #2, 4, and 5 must become prime.  3 and 6 must become composite
    odds = {x[-1] for x in values if len(x) in (2, 4, 5)}
    print(odds)

    start = time.time()

    permutations = []
    for (a1, a2, a3, a4, a5, a6), (b1, b2, b3, b4) in itertools.product(itertools.permutations("024568"), itertools.permutations("1379")):
        permutations.append((a1, a2, a3, b1, b2, b3, a4, a5, b4, a6))
    # ('8', '4', '6', '7', '3', '1', '5', '2', '9', '0')
    # permutations = itertools.permutations("0123456789")
    for value in values:
        offsets = [int(x) for x in value]
        is_prime = len(value) in (2, 4, 5)
        permutations = [p for p in permutations
                        if (tuple(p[offset] for offset in offsets) in PRIME_SET) == is_prime]
        print(value, len(permutations), time.time() - start)
    permutations = [p for p in permutations if all(x != y for x, y in zip(p, "0123456789"))]
    assert len(permutations) == 1
    print(permutations[0])
    return permutations[0]

# 12345678


if __name__ == '__main__':
    Magpie260.run()
