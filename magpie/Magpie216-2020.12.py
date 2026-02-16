from collections.abc import Iterable

from solver import Clue, ClueValue, Clues, EquationSolver, Evaluator, KnownLetterDict

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
        solver.solve(debug=False)

    def __init__(self):
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        for clue in clue_list:
            self.redo_evaluator(clue)
        super().__init__(clue_list, items=(range(-10, 11)))


    def redo_evaluator(self, clue: Clue):
        original_evaluator, = clue.evaluators
        evaluators = []
        for var in original_evaluator.vars:
            cubed_expression = clue.expression.replace(var, f'({var}**3)')
            evaluators.append(Evaluator.create_evaluator(cubed_expression))

        def my_wrapper(_evaluator: Evaluator, value_dict: KnownLetterDict
                       ) -> Iterable[ClueValue]:
            return {result for evaluator in evaluators
                    for result in evaluator(value_dict)}

        original_evaluator.set_wrapper(my_wrapper)


if __name__ == '__main__':
    Magpie216.run()
    pass
