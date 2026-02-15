from typing import Any

from misc.Pentomino import get_graph_shading
from solver import Clue, Clues, ConstraintSolver, EquationSolver

ACROSS = """
1 O(TV – W) – N (4) 
4 NTR – E (4) 
9 VIL–V (3)
11 NXS + I (4)
12 LW + X (3)
13 EE+TT (3)
14 LW+V (3)
16 GGGGGGGG – G (3)
18 LTR + U (4) 
20 GG + XX (3) 
22 I(G + I + I) (3) 
24 III + S (3)
27 GNLR + H – N (4)
28 HLL – O (3)
30 HO (3) 
32 II + XX – X (3)
34 EEO + E (3)
35 VOR + H (4)
36 (I + X)(I + V) (3)
37 FOU + R (4)
38 HOW + N (4)
"""

DOWN = """
2 L(X – I)(W – G) – N (4) 
3 HW + S (3) 
4 LW + H (3) 
5 S(H + I) – F (3) 
6 III + G (3) 
7 HOU – X (4)
8 GX(G+X)–GGI+G (4) 
10 (WN – R)(S + L + G) (4) 
15 EE + XX + W (3) 
17 IW–V (3) 
18 SX + L (3) 
19 EER + X (3) 
21 RX – S (3) 
23 USE – R – H (4) 
25 (FR + O)(H + S) (4) 
26 EOO+T (4) 
29 O(OI – T) + I (4) 
31 FV + RX (3) 
32 GX(V + V) + X – V (3)
33 FW – F (3) 
34 GIX – L (3)
"""

GRID = """
XXX.XXX.X
X.XX.X...
X..X..XX.
X.X.X.X..
XX.X.XX.X
XX....XX.
X.XXX.X..
X...X....
.X...X...
"""

class Magpie265 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 60))

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSS, DOWN, locations)
        return clues

    def draw_grid(self, location_to_entry, known_letters,
                  top_bars, left_bars, location_to_clue_numbers, **args: Any) -> None:
        substitution = [''] * 10
        for letter, value in known_letters.items():
            value = value % 26
            if 0 <= value <= 9:
                substitution[value] += letter
        location_to_entry = {location: substitution[int(value)]
                             for location, value in location_to_entry.items()}
        names = ["ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE",
                 "TEN", "ELEVEN", "TWELVE", "THIRTEEN", "FOURTEEN", "FIFTEEN", "SIXTEEN"]
        seen_across = set()
        seen_down = set()

        def find_spot(name):
            for row in range(1, 10):
                for column in range(1, 11 - len(name)):
                    if all(ch in location_to_entry[row, column + i] and (row, column + i) not in seen_across
                           for i, ch in enumerate(name)):
                        seen_across.update((row, column + i) for i in range(len(name)))
                        return Clue('', True, (row, column), len(name))
                    if all(ch in location_to_entry[column + i, row] and (column + i, row) not in seen_down
                           for i, ch in enumerate(name)):
                        seen_down.update((column + i, row) for i in range(len(name)))
                        return Clue("", False, (column, row), len(name))

        clue_to_value = {}
        for name in reversed(names):
            clue = find_spot(name)
            assert clue.length == len(name)
            assert (ch in location_to_entry[location] for ch, location in zip(name, clue.locations))
            for ch, location in zip(name, clue.locations):
                location_to_entry[location] = ch
            clue_to_value[clue] = name

        class Foobar(ConstraintSolver):
            def __init__(self):
                super().__init__(list(clue_to_value))

            def draw_grid(self, top_bars, left_bars, **args):
                solution = [clue.locations for clue in clue_to_value]
                shading = get_graph_shading(solution)
                super().draw_grid(shading=shading, top_bars=set(), left_bars=set(), **args)

        temp = Foobar()
        temp.plot_board(clue_to_value)


if __name__ == '__main__':
    Magpie265.run()
