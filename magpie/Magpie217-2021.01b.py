from typing import Unpack

from matplotlib import pyplot as plt, patches

from solver import Clues, Clue, ConstraintSolver, DrawGridArgs

EQUATIONS = """
"""

GRID = """
XXX.XX.XX.X
X....X.....
..X......X.
X.....X....
...X..X.....
X...X..X...
XX...X.....
XX.....X...
X.X....X..X
X....X...X.
...X.XX.X..
X..X..X....
...X.......
X......X...
X.....X....
"""

ACROSSES = """
1 7 ADDENDA
5 10 IDAEANVINE
9 6 INANGA
10 10 ENROLLMENT
11 8 NOTIONAL
13 8 CLOWNISH
14 9 KOWTOWERS
15 8 WRAWLING
17 9 NARROWING
19 5 MOMUS
20 7 TWINING
22 9 UPWINDING
24 10 BARROWLOAD
26 9 TRAINDOWN
28 5 THOWL
30 9 RESISTERS
31 12 METASTASISES
33 9 SWAGSHOPS
37 9 WATERCOWS
39 8 LEGACIES
40 8 HEIRDOMS
41 11 SWINGSHIFTS
42 6 REATAS
43 8 WARTWORT
44 10 WASPSWAITS
"""

DOWNS = """
1 9 WAISTCOAT
2 8 DALLIERS
3 8 WEDGWOOD
4 10 WAPINSHAWS
5 10 SWISSROLLS
6 7 SWALLOW
7 11 WALNUTWOODS
8 10 WINTHROUGH
12 11 STORMWINDOW
15 7 WRONGER
16 12 INNERPLANETS
18 10 INBREEDING
21 10 INEBRIATED
23 12 VETERINARIAN
25 5 ONTAP
27 9 ATTRAHENT
29 8 LITIGANT
32 9 NARCOTINE
34 8 SHORTEST
35 7 OLDBEAN
36 9 TASMANSEA
38 5 CHIOS
"""


class PrettyPrinter (ConstraintSolver):
    @staticmethod
    def run():
        solver = PrettyPrinter()
        solver.plot_board(solver.get_filled_in_clues())
        solver.verify_is_180_symmetric()

    def __init__(self):
        clues = self.get_clue_list()
        super().__init__(clues)

    @staticmethod
    def get_clue_list():
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for lines, letter, is_across in ((ACROSSES, 'a', True), (DOWNS, 'd', False)):
            lines = lines.strip().splitlines()
            for line in lines:
                x, y, word = line.split(' ')
                clue_number, length = int(x), int(y)
                actual_length = sum(x not in 'NSEW' for x in word)
                assert length == len(word)
                location = grid[clue_number - 1]
                clue = Clue(f"{clue_number}{letter}", is_across, location, actual_length, context=word)
                clues.append(clue)
        return clues

    def get_filled_in_clues(self):
        return {clue: ''.join(x for x in clue.context if x not in 'NSEW') for clue in self._clue_list}

    def draw_grid(self, **args: Unpack[DrawGridArgs]) -> None:
        """Override this method if you need to intercept the call to the draw_grid() function."""
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
        args['axes'] = axes
        rows = args['max_row']
        columns = args['max_column']
        super().draw_grid(**args)
        for row in range(1, rows):
            axes.plot([1, columns], [row + .5, row + .5], 'gray', linewidth=1)
        for column in range(1, columns):
            axes.plot([column + .5, column + .5], [1, rows], 'gray', linewidth=1)

        x, y = 17, 19
        axes.add_patch(patches.Rectangle((x / 2, y / 2), 0.5, 0.5, facecolor='lightblue', linewidth=0))

        for clue in self._clue_list:
            old_x, old_y = x, y
            word = clue.context
            x = old_x - word.count('W') + word.count('E')
            y = old_y - word.count('N') + word.count('S')
            axes.plot([old_x / 2 + 0.25, x / 2 + 0.25], [old_y / 2 + 0.25, y / 2 + 0.25], 'red', linewidth=2)


        plt.plot(())
        plt.show()


if __name__ == '__main__':
    PrettyPrinter.run()

