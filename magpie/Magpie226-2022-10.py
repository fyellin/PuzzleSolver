from __future__ import annotations

from solver import ClueValue, Clues, EquationSolver, Intersection
from solver import KnownClueDict, KnownLetterDict


def digit_sum(value: ClueValue | str | int) -> int:
    return sum(int(x) for x in str(value))


GRID = """
X.XXX
.X.X.
XX.X.
X.X.X
.X...
X.X..
"""

ACROSSES = """
1   (3)
3 EU (2) 
5 BBS (3)
7 BBO (3)
9 SUU (2)
10 36 (2)
11 CCOU (3)
13 CMUU (3)
14 BU (2)
15   (3)
"""

DOWNS = """
1 CFU (3)
2 BBMU (3)
4 C**6 + BM (3)
6 EUW – F (3)
8 C + E + RS (3)
10 E(F + M + S) (3)
11   (3)
12 E**2 + MSU (3)
"""


class Magpie226 (EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie226()
        # solver.solve(debug=True, max_debug_depth=200)
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSSES, DOWNS, grid)
        super().__init__(clues, items=(2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37))

    def check_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> bool:
        possible_values = [ClueValue(str(c + int(value))) for c in [known_letters['C']] for value in known_clues.values()]
        d11 = self.clue_named('11d')
        intersection1, = Intersection.get_intersections(d11, self.clue_named('11a'))
        intersection2, = Intersection.get_intersections(d11, self.clue_named('13a'))
        pattern = Intersection.make_pattern_generator(d11, [intersection1, intersection2], self)(known_clues)
        known_clues[d11] = next(x for x in possible_values if pattern.fullmatch(x))
        known_clues[self.clue_named('1a')] = ClueValue('159')
        known_clues[self.clue_named('15a')] = ClueValue('648')
        return True



def foobar():
    # top is 5.  bottom is 4
    for i in range(10):
        a = (10921 + 1000 * i, 12752, 42599)
        print(i, sum(a) ** 3)
    for j in range(10):
        b = (36204, 2347, 15608 + j * 10)
        print(j, sum(b) ** 3)

def foobar2():
    import math
    a = math.ceil(10000_00000_00000 ** (1/3))
    b = math.ceil(99999_99999_99999 ** (1/3))
    for value in range(a, b):
        top = value ** 3
        top1, top = divmod(top, 1_00000_00000)
        top2, top3 = divmod(top, 1_00000)
        value2 = top1 + top2 + top3
        bottom = value2 ** 3
        bottom1, bottom = divmod(bottom, 1_00000_00000)
        bottom2, bottom3 = divmod(bottom, 1_00000)
        if bottom1 + bottom2 + bottom3 == value:
            print(value, value**3, value2, value2**3)

if __name__ == '__main__':
    Magpie226.run()
    # foobar2()
