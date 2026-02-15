import itertools
import numpy as np

from misc.factors import factor_count
from solver import Clue, EquationSolver, Evaluator, Location


def create_factor_grid():
    grid = np.zeros((100, 100), dtype=int)
    for i, j in itertools.combinations(range(100), 2):
        grid[i, j] = grid[j, i] = factor_count(abs(i * i - j * j))
    return grid

TAGS = """AC AD BF
AH DE DG EH
BG CH
CE EG
AE
CD CF DH"""
lines = TAGS.splitlines()
lines = [line.split() for line in lines]

all_items = [item for line in lines for item in line]

#                                   A   B  C  D  E    F  G   H
#    lookup = dict(zip("ABCDEFGH", (6, 15, 5, 7, 10, 16, 12, 3)))
class Magpie269 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=100)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 100), allow_duplicates=True)
        self.add_constraints(clues)

    def get_clues(self):
        grid = create_factor_grid()
        clues = []
        for row, line in enumerate(lines):
            for letters in line:
                letter1, letter2 = letters
                clue_number = len(clues) + 1
                expression = f"  @grid [ {letter1}, {letter2} ]"
                clue = Clue(letters, True, (clue_number, 1), 1, context=(row, letters))
                clue.evaluators = Evaluator.create_evaluators(expression, mapping={'grid': grid})
                clues.append(clue)
        return clues

    def add_constraints(self, clues):
        for clue in clues:
            (row, name) = clue.context
            if row < 5:
                self.add_constraint((clue,), lambda x: int(x) < 8, name=f"{name}<8")
            else:
                self.add_constraint((clue,), lambda x: int(x) == 8, name=f"{name}=8")
        for clue1, clue2 in itertools.combinations(clues, 2):
            (row1, name1) = clue1.context
            (row2, name2) = clue2.context
            if row1 == 5 or row2 == 5: continue
            if row1 < row2:
                self.add_constraint((clue1, clue2), lambda x, y: int(x) < int(y), name=f"{name1}<{name2}")
            elif row1 == row2:
                self.add_constraint((clue1, clue2), lambda x, y: int(x) == int(y), name=f"{name1}={name2}")
            elif row1 > row2:
                self.add_constraint((clue1, clue2), lambda x, y: int(x) > int(y), name=f"{name1}>{name2}")



    def get_allowed_regexp(self, location: Location) -> str:
        return ".*"


if __name__ == '__main__':
    Magpie269.run()
