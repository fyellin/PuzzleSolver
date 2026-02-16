import math
import re
from typing import Any
from collections.abc import Sequence

from matplotlib import pyplot as plt

from solver import Clue, Clues, EquationSolver, Evaluator, Location

GRID = """
x...xxx..x....x
...x.x.x.x...
.x.xx.xx.xx
...xxx..x
xx.x.x.
x....
...
x
"""

HARVEST = """
7 PE – G, CUP (4)
9 AGLOW, A + GLOW (4)
11 AI – D, AID – ES (4) 
17 HO – E, CH – ANT (5)
18 AW + E, AW + L (4) 
19 O – NE, SABRE (4)
21 YEAR, PR + AY (4)
23 IS, NANNY (4) 
27 HAGGADA, HAGGAD + A (5)
"""

INUNDATION = """
1 BAA, SAY (5)
3 NEE/D, NEE (4)
5 AL – P, ALP (4)
8 BAN + S, BAN + D (4)
10 W + RITE, S + HOWS (4)
13 ANGOL – A, ALONG (4)
20 AS, I (4)
22 WEAN, WAT-ER (4)
26 NAY, LAY (5)
"""

PLANTING = """
2 WI - NG, WIN + O (5)
4 MY, I + S (4)
6 FU + NNY, C + UBE (5)
12 BLABBE - D, BLABBE - R (4)
14 SO, BAG (4)
15 EA, LEA (4)
16 GRAD-ED, FARM+S (4)
24 AN, NANA (4)
25 AF - T, DICE (4)
"""

def my_div(a, b):
    if b == 0:
        raise ZeroDivisionError
    q, r = divmod(a, b)
    if r == 0:
        return q
    raise ArithmeticError

def choose(x, y):
    if x < 0 or y < 0 or y < x:
        raise ArithmeticError
    return math.comb(y, x)

class Solver236(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Solver236()
        solver.solve(debug=True)

    def __init__(self) -> None:
        super().__init__(self.get_clue_list(), items=range(1, 21))

    MAPPING = { 'choose': choose, 'div': my_div }

    @classmethod
    def get_clue_list(cls) -> Sequence[Clue]:
        grid_locations = Clues.get_locations_from_grid(GRID)

        clues = []
        for lines, is_across, letter in ((INUNDATION, True, 'i'), (HARVEST, False, 'h'), (PLANTING, False, 'p')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number, equations, length = int(match.group(1)), match.group(2), int(match.group(3))
                eq1, eq2 = equations.split(',')
                (row, column) = grid_locations[number - 1]
                if letter == 'i':
                    locations = [(row, column + i) for i in range(length)]
                elif letter == 'h':
                    locations = [(row, column)]
                    while len(locations) < length:
                        row, column = (row, column - 1) if column % 2 == 0 else (row - 1, column + 1)
                        locations.append((row, column))
                else:
                    locations = [(row, column)]
                    while len(locations) < length:
                        row, column = (row, column - 1) if column % 2 == 1 else (row + 1, column - 1)
                        locations.append((row, column))
                clue = Clue(f'{number}{letter}', is_across, (row, column), length, locations=locations)
                clue.evaluators = Evaluator.create_evaluators(
                    f'"choose"({eq1}, {eq2})', mapping=cls.MAPPING)
                clues.append(clue)
        return clues

    def draw_grid(self, *,
                  location_to_entry: dict[Location, str],
                  location_to_clue_numbers: dict[Location, Sequence[str]],
                  shading: dict[Location, str] = None,
                  **args: Any) -> None:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([1, 9, 9, 1])
        aspect_ratio = math.sqrt(3)/2
        axes.set_aspect(aspect_ratio)
        axes.axis('off')

        def draw_heavy(row, column, where: str | tuple[str, str], color: str = 'black'
                       ) -> None:
            is_point_up = column % 2 == 0
            point_row, flat_row = (row, row + 1) if is_point_up else (row + 1, row)
            center_x = (1 + row + column) / 2.0
            if isinstance(where, tuple):
                where = where[0] if is_point_up else where[1]
            args = dict(color=color, linewidth=5)
            if where == 'left':
                if column != 1:
                    axes.plot([center_x, center_x - .5], [point_row, flat_row], **args)
            elif where == 'right':
                if column + 2 * row != 17:
                    axes.plot([center_x, center_x + .5], [point_row, flat_row], **args)
            elif where in ('top', 'bottom'):
                if is_point_up or row != 1:
                    axes.plot([center_x - .5, center_x + .5], [flat_row, flat_row], **args)

        locations = { location for clue in self._clue_list for location in clue.locations}

        text_args = dict(verticalalignment='center', horizontalalignment='center',
                         fontsize=20, fontfamily="sans-serif", fontweight='bold')
        label_args = dict(fontsize=10, fontfamily="sans-serif", fontweight='bold')

        for (row, column), entry in location_to_entry.items():
            color = '#FF000060'
            if entry in '365':
                center_x = (1 + row + column) / 2.0
                if column % 2 == 1:
                    axes.fill([center_x, center_x - .5, center_x + .5, center_x], [row + 1, row, row, row + 1],
                              color=color)
                else:
                    axes.fill([center_x, center_x - .5, center_x + .5, center_x], [row, row + 1, row + 1, row],
                              color=color)

        for row, column in locations:
            value = location_to_entry.get((row, column))
            label = location_to_clue_numbers.get((row, column))
            center_x = (1 + row + column) / 2.0
            if column % 2 == 1:
                axes.plot([center_x, center_x - .5, center_x + .5, center_x], [row + 1, row, row, row + 1],
                          color='black')
                if value:
                    axes.text(center_x, row + .5, value, **text_args)
                if label:
                    axes.text(center_x - .4, row + .05, str(label[0]),
                              verticalalignment='top', horizontalalignment='left', **label_args)
            else:
                axes.plot([center_x, center_x - .5, center_x + .5, center_x], [row, row + 1, row + 1, row],
                          color='black')
                if value:
                    axes.text(center_x, row + .7, value, **text_args)
                if label:
                    axes.text(center_x, row + .15, str(label[0]),
                              verticalalignment='top', horizontalalignment='center', **label_args)

        for clue in self._clue_list:
            if clue.name.endswith("i"):
                draw_heavy(*clue.locations[0], 'left')
                draw_heavy(*clue.locations[-1], 'right')
            elif clue.name.endswith("h"):
                draw_heavy(*clue.locations[0], ('bottom', 'right'))
                draw_heavy(*clue.locations[-1], ('left', 'top'))
            elif clue.name.endswith("p"):
                pass
                draw_heavy(*clue.locations[0], ('right', 'top'))
                draw_heavy(*clue.locations[-1], ('bottom', 'left'))
        draw_heavy(1, 10, 'bottom')
        draw_heavy(3, 2, 'right')
        draw_heavy(5, 5, 'right')

        plt.show()


if __name__ == '__main__':
    Solver236().run()

