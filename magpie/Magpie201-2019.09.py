from typing import Unpack
from collections.abc import Sequence

from solver import Clue, Clues, DrawGridArgs, Location, EquationSolver

ACROSS = """
1 JE(RK + S) (4)
4 SEAM (3)
7 CAGE (4)
10 EXTEND (5)
11 PUN(IS + H + ES) (5)
12 TEST = K (2)
13 WEE(K – N – I + GH + T – S) (5)
16 CE(D – E) (3)
18 ENG(IN + EE – R + S) (4)
20 TRUCE (4)
23 QUE(ST – S) (3)
25 SHINED (5)
27 TA + N (2)
28 OPE(RA – T – O + R) (5)
29 CU(TL + E + R)Y (5)
31 (S + K – I)NNY (4)
32 STAG (3)
33 JI(L + T + S) (4)
"""


DOWN = """
1 ERRED (4)
2 TEETERS (3)
3 N(O – U)N (2)
4 TOOT (3)
5 TEE = Q (2)
6 FR(O + NT) (4)
7 YEN (3)
8 BUS (3)
9 GEM (3)
13 SERIES (3)
14 ZE + A – L (2)
15 J(E + TTI – S – O)N (3)
17 FAT (3)
19 RAVE (4)
20 (V + I)E (2)
21 PUSH (4)
22 JE(S – TE + D) (3)
23 NIX (3)
24 RYE (3)
26 CUT (3)
27 CITE (3)
29 TERR – O + R (2)
30 H(A – L + E) (2)
"""

GRID = """
XX.XXXXX.XX
.X....X....
X.XX.X.XX..
X...X..X..X
XX.XX.X..X.
X....X.X...
X...X..X...
"""


class MySolver(EquationSolver):
    def draw_grid(self, **args: Unpack[DrawGridArgs]) -> None:
        location_to_entry: dict[Location, str] = args['location_to_entry']
        args['shading'] = {
            location: 'lightblue' for (location, value) in location_to_entry.items() if value in '378'
        }
        super().draw_grid(**args)


def create_clue_list() -> Sequence[Clue]:
    locations = Clues.get_locations_from_grid(GRID)
    return Clues.create_from_text(ACROSS, DOWN, locations)


def run() -> None:
    clue_list = create_clue_list()
    solver = MySolver(clue_list, items=list(range(1, 27)))
    solver.verify_is_180_symmetric()
    solver.solve(debug=False)


if __name__ == '__main__':
    run()
