from collections.abc import Iterable
from typing import Iterator

from solver import Clues, EquationSolver, ClueValue, Evaluator, Letter

GRID = """
X.XXXX
XXX...
X..XX.
X.X..X
X.X.X.
X..X..
"""

ACROSS = """
1 SRRX + U/R – R – E (3)
3 TIE + ISH (3)
6 AN + BO – CP + DQ + ER + FS (2)
8 RIN + GOT (4)
9 TO+WHH (4)
11 REEE – I (2)
12 OR/U – QQ + C (2)
13 WN + DLT (4)
15 S – SAAS – BB + CCI (4)
17 AX – L/W (2)
18 TR – U (3)
19 AQ + BR – CS + FP + EO + DN (3)
"""

DOWN = """
1 C + TO + RR – OOO (3)
2 OOOO – O – O (4)
3 L – G/H (2)
4 U + EEEEE – S (5)
5 MIXT + TO – OO (3)
7 N – LITT/M (5) 
10 STROON + OP + I  (4)
12 AO + CT (3)
14 (T + L) / O (3)
16 NE (2)
"""


class Magpie216(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie216()
        solver.solve(debug=True)

    def __init__(self):
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)

        def my_wrapper(evaluator: Evaluator, value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
            for cubed_letter in evaluator.vars:
                temp = self._known_letters[cubed_letter]
                self._known_letters[cubed_letter] = temp ** 3
                results = list(Evaluator.standard_wrapper(evaluator, value_dict))
                self._known_letters[cubed_letter] = temp
                yield from results

        for clue in clue_list:
            clue.evaluators = tuple(x.with_alt_wrapper(my_wrapper) for x in clue.evaluators)

        super().__init__(clue_list, items=(range(-10, 11)))


if __name__ == '__main__':
    Magpie216.run()
    pass
