import itertools
from datetime import datetime
from typing import Dict, Sequence, Iterable

from GenericSolver import SolverByLetter
from Clue import Location, Letter, ClueList


class MySolver(SolverByLetter):
    def get_letter_values(self, known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = set(known_letters.values())
        for next_letter_values in itertools.permutations(range(1, 17), count):
            if all(v not in current_letter_values for v in next_letter_values):
                yield next_letter_values

    def check_and_show_solution(self, known_letters: Dict[Letter, int]) -> None:
        super(MySolver, self).check_and_show_solution(known_letters)
        self.clue_list.draw_board(self.known_clues)
        # print(eval('I*R*R*A*N*E, I, P*I', None, known_letters))
        # print(eval('T*E*S*S*E*R, A, C*T', None, known_letters))
        # print(eval('D*O*D*E*C*A, G, O*N', None, known_letters))
        # print(known_letters)


# noinspection SpellCheckingInspection
ACROSS = """
1 ON (2)
2 S + (A + L)E (2)
4 ABB (3)
6 B – A (2)
7 MARS + ALA (3)
9 T + REE (2)
10 ARG + O + T (2)
12 GL + IB (3)
14 DEGR/(EES) (2)
15 BAN – E (3)
16 PO – SE (2)
17 AGRAR + IAN (3) 
19 R + O + LE (2)
21 SCA – B (2)
24 SPR + ITE (3)
27 T + A + LE (2)
28 UNC + OS (3)
29 BE + N – S (2)
30 SAI + L (2)
"""

# noinspection SpellCheckingInspection
DOWN = """
1 A(MB – O)S (3)
2 G + ALLS (3)
3 BAA (2)
4 ARE – A (2)
5 BR + E + R (2)
6 BRAG – GART (3)
8 RAG (2)
11 PAGEA – NTS (3)
12 T + O (2)
13 US (2)
14 UR (2) 
15 AGA (2)
16 ARRESTE/D (3) 
18 EL + M (2)
20 DAT + ES (3)
22 CL + AMP (3)
23 TI – L + E (2)
25 EL – E + A (2)
26 L + AG (2)
"""

LOCATIONS: Sequence[Location] = (
             (1, 1), (1, 3), (1, 4), (1, 5), (1, 7),
             (2, 2), (2, 4), (2, 6), (3, 1), (3, 3),
             (3, 4), (3, 5), (3, 7), (4, 1), (4, 3),
             (4, 6), (5, 1), (5, 2), (5, 4), (5, 5),
             (5, 6), (5, 7), (6, 1), (6, 2), (6, 3),
             (6, 4), (6, 5), (7, 1), (7, 4), (7, 6))


def run() -> None:
    clue_list = ClueList.create_from_text(ACROSS, DOWN, LOCATIONS)
    clue_list.verify_is_four_fold_symmetric()
    time1 = datetime.now()
    solver = MySolver(clue_list)
    solver.solve()
    time3 = datetime.now()
    print(solver.count_total, time3 - time1)


if __name__ == '__main__':
    run()
