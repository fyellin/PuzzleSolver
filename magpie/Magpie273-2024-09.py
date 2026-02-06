from __future__ import annotations

from typing import Any

from solver import ClueValue, Clues, EquationSolver


def digit_sum(value: ClueValue | str | int) -> int:
    return sum(int(x) for x in str(value))


GRID = """
XX.XX.X.
.X..XX.X
X.X..XX.
.X.XX.X.
XX..X..X
X.X..X..
"""

ACROSSES = """
1 UDDER (3)
3 S(HEL + TE) + R (3)
5 (E + U + L)ER (2)
6 A(DDE + ND + U − M) (3)
7 D(E + AR)LY (4)
10 OL + D (2)
11 TO + O (3)
12 FEE (2)
14 ODE (2)
15 RARE (3)
17 TEE (2)
18 (H + O + S + TE)**L (4)
20 EBB (3)
22 SEA (2)
23 YALE (3)
24 MO (3)
"""

DOWNS = """
1 BED (2)
2 OD**DS + ARE + (SE**VEN + T)O + ONE (4)
3 LOR − D (3)
4 FOES (3)
5 OLD + O − DE (2)
8 REAS + O − N + A + B − L − Y (3)
9 (T + O)(O + T) (3)
10 (H + E)(LEN + A) (3)
11 EV(E + N + S) (3)
13 ES(T + E)((R − A)**S + ES) (4)
15 VOLU + N + T + A − R + Y (3)
16 ED**DY + LA(D + Y) (3)
19 NO/(EL) (2)
21 SUE (2)
"""

class Magpie273 (EquationSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        solver.solve()

    def __init__(self) -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSSES, DOWNS, grid)
        super().__init__(clues, items=range(1, 17))

    def draw_grid(self, location_to_entry, **args: Any) -> None:
        l2 = {location: '●' if x in "24680" else ' ' for location, x in location_to_entry.items()}
        super().draw_grid(location_to_entry=l2, subtext="TAKE A BOW", **args)


if __name__ == '__main__':
      Magpie273.run()
