import itertools
import re

from solver import Clue, EquationSolver
from solver.equation_solver import KnownClueDict, KnownLetterDict
from solver.fill_in_crossword_grid import FillInCrosswordGridMushed

CLUES = """
E G (2) 
O K**B + K + B (2) 
E HJK (2) 
L B**B (2) 
C FF – H (2) 
N GE/K + H (2) 
K O ( C + L) (2) 
F H + JL (2) 
P P( B + D ) (3) 
O IN – H (3)
H B + DI (3) 
M E**K (3) 
G KMM (3) 
A K**P (3) 
I AO ( O + N ) (3) 
B AFN + M (3) 
H I**B + P (4) 
D K**M (4) 
L E**B (4) 
J NNN (4)
"""


class Magpie238(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie238()
        solver.solve(debug=False)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 17))

        for a, b in itertools.combinations(clues, 2):
            self.add_constraint((a, b), lambda x, y: int(x) < int(y))
            if a.context == b.context:
                self.add_constraint((a, b), lambda x, y: x[0] == y[0])


    def get_clues(self):
        result: list[Clue] = []
        for i, line in enumerate((l for l in CLUES.splitlines() if l), start=1):
            match = re.fullmatch(r'(\w) (.+) \((\d)\)', line.strip())
            assert match
            letter, expression, length = match.group(1, 2, 3)
            length = int(length)
            clue = Clue(str(i), True, (i, 1), length, expression=expression, context=letter)
            result.append(clue)
        return result

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        result = [(known_letters[clue.context], known_clues[clue])
                  for clue in self._clue_list]
        result.sort()
        filler = FillInCrosswordGridMushed(result, width=6, height=5)
        results = filler.run(debug=3, black_squares_okay=False, numbering=True)
        if results:
            self.show_letter_values(known_letters)

        for result in results:
            filler.display(result)


if __name__ == '__main__':
    Magpie238.run()
