import itertools
from collections.abc import Sequence
from typing import Unpack
import numpy as np

from misc.primes import PRIMES
from solver import Clue, Clues, DrawGridArgs, EquationSolver, KnownClueDict, \
    KnownLetterDict

GRID = """
XX.XXXXX
X.XX.X..
X..XX..X
X.X.XXX.
.XX..XX.
X..XX.XX
X..X....
"""

ACROSS = """
2 Po + WE + r (4) 
5 S + E + rIe/S (3) 
8 S + Um/S (2)
10 T + a − U (2)
11 P + r + I + m + e (3)
12 F + o − r − TY (3)
13 S + P + H + e + r + e (3) 
16 P + O + W − E + r (2) 
17 S + U + m (2)
18 S + IG/M + A (2)
20 S + I + G + m + A (2) 
22 SEr − I + e + S (3)
23 M + E + NUS (3)
25 SUm (3)
26 S + UM = O (2)
28 P + R − I + M − e (2)
30 T + H + e = TIM + E + S (3)
31 MINTY (4)
"""

DOWN = """
1 S + U + mS (2) 
2 mOr + e (3)
3 S + U + M (2)
4 S − IG/M + a (2) 
5 SE/r + I + ES (3) 
6 PR/I + Me (3)
7 F − E + W − e + R (2) 
9 RAT/I + o (3)
12 R + A − T − I + o (3) 
13 S + I + N + ES (3) 
14 −TE + RM (3)
15 ma + T + H (3)
19 C + O + S + IN + E (3) 
21 −T + rIG (3)
22 S − E + RI − eS (3) 
24 N(A + r) − C (3)
25 YY + Y = I − S (2)
26 SYS = S(I − S) (2)
27 M + E = T − I + C (2) 
29 N + U + m + S (2)
"""


class Listener4712(EquationSolver):
    @staticmethod
    def run() -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSS, DOWN, grid)
        solver = Listener4712(clues)
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self, clues: Sequence[Clue]):
        items = set()
        for prime in itertools.takewhile(lambda x: x < 200, PRIMES):
            value = 1
            while value < 200:
                items.add(value)
                value *= prime
        super().__init__(clues, items=sorted(items))

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict
                      ) -> None:
        super().show_solution(known_clues, known_letters)
        info = sorted((int(value), letter) for letter, value in known_letters.items())
        message = ''.join(letter for _, letter in info)
        print(message)

    # Sequence 1 (power of 4): 493,68-98,160-49,8114,43-54,12-18,41-14,514,882,8208
    # Sequence 2 (power of 3): 845, 701, 344, 155, 251, 134, 92, 737, 713, 371
    # Sequence 3 (power of 5): 472, 17-863, 575-95, 85-231, 36-169, 748-45, 547-48.
    def draw_grid(self, clue_values, **args: Unpack[DrawGridArgs]) -> None:
        shading = {}
        for clue, value in clue_values.items():
            if int(value) in (845, 472):
                shading |= {location: (1, 0, 0, .8) for location in clue.locations}

        def extra(_plt, axes):
            axes.plot([1, 1, 9, 9], [8, 9, 9, 8], 'black', linewidth=5)
            x_points = np.linspace(1, 9, 7)
            for x in (x_points[2], x_points[4]):
                axes.plot([x, x], [8, 9], 'black')
            font_info = dict(fontsize=30, fontweight='bold', fontfamily="sans-serif",
                             va='center', ha='center')
            for v, x in zip((371, 8208, 54748), x_points[1::2]):
                axes.text(x, 8.5, str(v), **font_info)

        super().draw_grid(extra=extra, shading=shading, **args)


if __name__ == '__main__':
    Listener4712.run()
