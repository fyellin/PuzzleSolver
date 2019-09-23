"""
get_letter_values:  Each digit can be used more than once.
is_zero_allowed:    This puzzle doesn't allow 0 in any intersection
"""

from typing import Dict, Sequence, Iterable

from ClueList import ClueList
from ClueTypes import Location, Letter
from EquationSolver import EquationSolver


class MySolver(EquationSolver):
    def __init__(self, clue_list: ClueList):
        super().__init__(clue_list, items=list(range(1, 10)))

    def get_letter_values(self, known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        return self.get_letter_values_with_duplicates(known_letters, count, 2)


class MyClueList(ClueList):
    def is_zero_allowed(self, location: Location) -> bool:
        return not(self.is_start_location(location) or self.is_intersection(location))


# noinspection SpellCheckingInspection
ACROSS = """
1 (ONE – (O/R + TOTH)E)R (3)
3 ON/E – OR(T – W – O) (3)
5 DEV(I + L/(AND)) (3)
7 D + E + E + P + S – E – A (2)
9 (W^H)IC(H + L + E)(T + T + E) + (RIS + (W – H)I)C – H (5)
11 WAL + ES (2)
13 (((H + O)/R)N)^S + (O + F + A + (D + I)(L^E – M))M + A (9)
15 E + I – T + H^(E + R) – O – R (3)
17 ALTER(N + A – T + I – V) + E (3)
18 J + O(IN – T) (3)
20 C(H + A) – RA(C – TERS) (3)
22 (FRE + ED – O)M – (O + F) – (C + H + O + I + C – E) (3)
"""


# noinspection SpellCheckingInspection
DOWN = """
1 ((C + A + T)C)^H + 22 (2)
2 S + WI – T + CH = SW + I/(TC) – H (2)
4 (SELE – C)(T + (I/O)) – N (3)
5 ((FREE + C)/(H/O) – I)CE (4)
6 (PR)^E + D + I(CAM – E)(N + T) (4)
7 A + (L + P + (H + A + C)(O – D))E (3)
8 C/H + OO(S + E) (3)
9 (PROA – IRE)S + IS (3)
10 (S + P(O + T + T))HE (3)
11 (DIFFER + E – N)/(CE) (3)
12 (THIS – O)(R + TH) – AT (3)
14 (T + V)S/E + R + I/E + S (2)
15 VI + (CE + V)ER + S – A (3)
16 O + P + T + (I + O)N (3)
19 S(O – R) + T (2)
20 T + H(E + PAI(R + S)) (3)
21 (W(H + I) + C)H (3)
"""


LOCATIONS = """
...X.X...
...XX....
...X.X...
XXX...XXX
.........
X...X....
...X.X...
...X.....
...XX....
...X.X...
.........
...X.....
"""


def run() -> None:
    locations = MyClueList.get_locations_from_grid(LOCATIONS)
    clue_list = MyClueList.create_from_text(ACROSS, DOWN, locations)
    clue_list.verify_is_vertically_symmetric()
    solver = MySolver(clue_list)
    solver.solve(debug=True)


if __name__ == '__main__':
    run()
