import itertools
from typing import Any

from solver import Clue, ClueValue, Clues, EquationSolver

GRID = """
XXXXXXXX
X...X...
X..X....
.X...X..
X.XX.X..
.X...XX.
X...X...
X..X....
"""

ACROSS = """
1 T + T + W + y (5)
7 b + b (2)
9 I + N (4)
10 E + S + T + T (4)
11 D − o − o − Y (3)
12 i + J − E − E (4)
13 i + s + s − N (4)
14 d − e − e − P (3)
15 b + U + U + Y (3)
17 B − l − l − s (4)
19 H − E − l (4)
20 S − U (3)
22 U + U + y − E (4)
23 A − G − G (4)
24 b + J (2)
25 D − S − Y (5)
"""

DOWN = """
2 U − b (3)
3 R − O (4)
4 s + s − T (2)
5 Ns − J (6)
6 E + L (4)
7 YYY (5)
8 BP + o + o (7)
9 Et + E + L (7)
12 bF + F + S (6)
13 JJ + e + B (5)
16 i + J (4)
18 B + J + J − E (4)
21 P + T − s (3)
23 U − Y (2)
"""


class Listener4816(EquationSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        # solver.verify_is_180_symmetric()
        # solver.plot_board()
        solver.solve(debug=False    )

    def __init__(self) -> None:
        clues = self.get_clues()
        items = list(itertools.takewhile(lambda x: x <= 100_000, (i**3 for i in itertools.count(1))))
        print(items)
        super().__init__(clues, items=items)

    def get_clues(self):
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSS, DOWN, grid)
        return clues

    def plot_board(self, clue_values: dict[Clue, ClueValue] | None = None,
                   **more_args: Any) -> None:
        table = str.maketrans("123456789", "ottffssen".upper())
        if clue_values is not None:
            clue_values = {clue: value.translate(table) for clue, value in clue_values.items()}
        super().plot_board(clue_values, **more_args)

"""
By Just spelling it.
By head of word.
A     B     D     E     F     G     H     I     J     L     N     O     P     R     S     T     U     W     Y     b     d     e     i     l     o     s     t     y    
19683 9261  79507 1000  42875 4913  12167 2744  64    2197  3375  54872 729   64000 512   343   125   50653 27    8     32768 15625 5832  1331  39304 216   6859  10648

b     Y     J     U     s     T     S     P     E     l     L     I     N     G     i     t     B     y     H     e     A     d     o     F     W     O     R     D    
8     27    64    125   216   343   512   729   1000  1331  2197  2744  3375  4913  5832  6859  9261  10648 12167 15625 19683 32768 39304 42875 50653 54872 64000 79507

"""


if __name__ == '__main__':
    Listener4816.run()
