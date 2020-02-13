import re

from solver import Clues, EquationSolver

GRID = """
XXXXXX
X..X..
XX.XX.
X.XX.X
XX.XX.
X.X.X.
"""

ACROSS = """
1 (BJ + DL)(BJ – DL) (2)
3 (EK + BH)(EK – BH) (2)
5 (JK + CI)(JK – CI) (2)
7 (AG + FL)(AG – FL) (3)
8 (IJ + EK)(IJ – EK) (3)
9 (JK + CD)(JK – CD) (3)
11 (HK + AG)(HK – AG) (3)
13 (EF + CK)(EF – CK) (3)
15 (DH + EK)(DH – EK) (3)
17 (EK + DJ)(EK – DJ) (3)
19 (DH + GL)(DH – GL) (3)
21 (IL + CG)(IL – CG) (2)
22 (GL + CD)(GL – CD) (2)
23 (BH + DJ)(BH – DJ) (2)
"""

DOWN = """
1 (GJ + BL)(GJ – BL) (3)
2 (AK + CG)(AK – CG) (2)
3 (DJ + BL)(DJ – BL) (3)
4 (EF + AI)(EF – AI) (3)
5 (JK + AB)(JK – AB) (2)
6 (DE + FL)(DE – FL) (3)
10 (BJ + AK)(BJ – AK) (2)
12 (EK + AI)(EK – AI) (2)
13 (DH + CF)(DH – CF) (3)
14 (DE + BL)(DE – BL) (3)
15 (HK + CF)(HK – CF) (3)
16 (AG + CK)(AG – CK) (3)
18 (FL + AB)(FL – AB) (2)
20 (GL + AB)(GL – AB) (2)
"""

ACROSS = re.sub("\(\w\w \+ \w\w\)", "", ACROSS)
DOWN = re.sub("\(\w\w \+ \w\w\)", "", DOWN)

# A C E H J L
# B D F G I K

class MySolver(EquationSolver):
    @staticmethod
    def run() -> None:
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        solver = MySolver(clue_list, items=(2, 3, 5, 7, 11, 13, 4, 9, 25, 49, 121, 169))
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

if __name__ == '__main__':
    MySolver.run()
