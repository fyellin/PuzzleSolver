from typing import Any

from misc import number_to_words
from misc.Pentomino import get_graph_shading
from solver import Clues, DancingLinks, EquationSolver

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

    def draw_gridx(self, location_to_entry, known_letters,
                  top_bars, left_bars, location_to_clue_numbers, **args: Any) -> None:
        substitution = [''] * 10
        for letter, value in known_letters.items():
            value = value % 26
            if 0 <= value <= 9:
                substitution[value] += letter
        location_to_entry = {location: substitution[int(value)]
                             for location, value in location_to_entry.items()}
        constraints = {}
        for i in range(1, 17):
            name = number_to_words(i).upper()
            for u in range(1, 10):
                for v in range(1, 11 - len(name)):
                    if all(ch in location_to_entry[u, v + i] for i, ch in enumerate(name)):
                        constraints[u, v, 'A', name] = [name, *(f'r{u}c{v + i}' for i in range(len(name)))]
                    if all(ch in location_to_entry[v + i, u] for i, ch in enumerate(name)):
                        constraints[v, u, 'D', name] = [name, *(f'r{v + i}c{u}' for i in range(len(name)))]
        super_draw = super().draw_grid

        def row_printer(output):
            solution = []
            location_to_letter = {}
            for (row, column, direction, name) in output:
                dr, dc = (0, 1) if direction == 'A' else (1, 0)
                squares = [(row + i * dr, column + i * dc) for i in range(len(name))]
                solution.append(squares)
                location_to_letter.update(zip(squares, name, strict=True))
            shading = get_graph_shading(solution)
            super_draw(shading=shading, top_bars=set(), left_bars=set(),
                       location_to_entry=location_to_letter, **args)

        solver = DancingLinks(constraints, row_printer=row_printer)
        solver.solve(debug=10)


if __name__ == '__main__':
    Magpie265.run()
