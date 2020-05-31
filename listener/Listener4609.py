import itertools
from typing import Sequence, Set, Dict, Any

from solver import Clue, EquationSolver, Clues, Location

GRID = """
XX.X.XX.X.XX
X.......X...
.X..X....X..
X.X....X....
...X........
X....X.X....
XX....X....X
..XX....X.X.
X.....X..X..
....X.......
X...X.......
X.....X.....
"""

ACROSS = """
1 0 (6)
5 0 (6)
9 9 (8)
10 0 (4)
11 0 (7)
14 0 (3)
16 0 (5)
17 0 (7)
18 0 (6)
20 0 (5)
21 0 (5)
23 0 (6)
25 0 (7)
29 0 (5)
31 0 (3)
32 0 (7)
33 0 (4)
34 0 (8)
35 0 (6)
36 0 (6)
"""

DOWN = """
1  0 (6)
2 0 (5)
3 0 (5)
4 0 (4)
5 0 (7)
6 (0) (5)
7 0 (6)
8 0 (6)
12 0 (5)
13 0 (7)
15 0 (7)
19 0 (7)
20 0 (5)
21 0 (6)
22 0 (6)
24 0 (6)
26 0 (5)
27 0 (5)
28 0 (5)
30 0 (4)
"""

class Listener4609(EquationSolver):
    @staticmethod
    def run():
        solver = Listener4609()
        solver.plot_board({})
        solver.verify_is_180_symmetric()

    def __init__(self) -> None:
        clue_list = self.make_clue_list()
        super(Listener4609, self).__init__(clue_list)

        array = [' '] * 144
        index = 0
        for letter in ''.join(self.WORDS):
            assert array[index] == ' '
            array[index] = letter
            index += ord(letter) + 1 - ord('A')
            index %= 144
        self.array = array

    def make_clue_list(self) -> Sequence[Clue]:
        locations = Clues.get_locations_from_grid(GRID)
        return Clues.create_from_text(ACROSS, DOWN, locations)

    def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                  location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
                  top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:

        for letter, (row, column) in zip(self.array, itertools.product(range(1, 13), repeat=2)):
            location_to_entry[row, column] = letter
        circles = {(8, 1)}
        super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number, top_bars,
                          left_bars,
                          circles=circles, **more_args)

    WORDS = [
        "MUM",
        "FAT",
        "INLY",
        "SLOT",
        "JINGO",
        "OSMIC",
        "BLAER",
        "MALMO",
        "AMOMUM",
        "OUTGAS",
        "FANGOS",
        "LIMNER",
        "EXTORT",
        "HELENA",
        "DUSTMAN",
        "SWANAGE",
        "EDGWARE",
        "GLASGOW",
        "THETFORD",
        "STDAVIDS",
        "SHEPTONMALLET",
        "BUDLEIGHSALTERTON",
    ]



if __name__ == '__main__':
    Listener4609.run()

