"""
get_letter_values:  Each digit can be used more than once.
is_zero_allowed:    This puzzle doesn't allow 0 in any intersection
"""


import itertools
from datetime import datetime
from typing import Dict, Sequence, Iterable

from GenericSolver import SolverByLetter
from Clue import Location, Letter, ClueList


class MySolver(SolverByLetter):
    def get_letter_values(self, known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        return self.get_letter_values_n_impl(1, 9, 2, known_letters, count)

    def is_zero_allowed(self, location: Location) -> bool:
        return not self.clue_list.is_start_location(location) and not self.clue_list.is_intersection(location)


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

LOCATIONS: Sequence[Location] = (
    (1, 4), (1, 6), (2, 4), (2, 5), (3, 4), (3, 6),
    (4, 1), (4, 2), (4, 3), (4, 7), (4, 8), (4, 9),
    (6, 1), (6, 5), (7, 4), (7, 6), (8, 4),
    (9, 4), (9, 5), (10, 4), (10, 6), (12, 4))


def run() -> None:
    clue_list = ClueList.create_from_text(ACROSS, DOWN, LOCATIONS)
    clue_list.verify_is_vertically_symmetric()
    if True:
        time1 = datetime.now()
        solver = MySolver(clue_list)
        solver.solve()
        time3 = datetime.now()
        print(solver.count_total, time3 - time1)


if __name__ == '__main__':
    run()
