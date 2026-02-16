import itertools
import re
from typing import Unpack

from misc.factors import factor_list
from solver import Clue, Clues, ConstraintSolver, DrawGridArgs, generators

GRID = """
XXXXX.XX
X....X..
X......X
X.....X.
XX..X...
X...X...
"""

# X, Y, Z = (276, 403, 1964)

ACROSS = """
1 6Y  (4)
5 X + 17a (4) 
8 18X – 14d (4)
9 Multiple of 15d  (3)
10 3Z**2 (8)
12 X**3 (8)
14 2d + 14d – X (3)
16 Y + 13d (4)
17 X + Z + 11d + 15d (4)
18 Y + Z + 9a + 15d  (4)
"""

DOWN = """
2 Factor of Z (3)
3 36Y (5)
4 2010X + 154Z (6)
5 1237X  (6)
6 Factor of X  (2)
7 Multiple of 6d (2)
8 X + 9a + 6d (3)
9 14d × 14d × (14d + 6d)  (5)
11 2Y + 6d + 7d + 14d (3)
13 X + Y + 14d (3)
14 Factor of X (2)
15 Factor of Y (2)
"""

def playground():
    def print_start_info(XX, YY, ZZ):
        print(f'X {min(XX)}-{max(XX)} ({len(XX)})')
        print(f'Y {min(YY)}-{max(YY)} ({len(YY)})')
        print(f'Z {min(ZZ)}-{max(ZZ)} ({len(ZZ)}) {len(X) * len(Y) * len(Z)}')

    def print_info(info):
        XX = {x for x, _, _ in info}
        YY = {y for _, y, _ in info}
        ZZ = {z for _, _, z in info}
        print(f'X {min(XX)}-{max(XX)} ({len(XX)})')
        print(f'Y {min(YY)}-{max(YY)} ({len(YY)})')
        print(f'Z {min(ZZ)}-{max(ZZ)} ({len(ZZ)}) {len(info)}')

    Y = [y for y in range(3000)
         if 1000 <= 6 * y <= 9999       # 1A
         if 10_000 <= 36 * y <= 99_999  # 3D
         if 2 * y + 33 <= 999           # 11D
         if str(6 * y)[2] == str(36 * y)[0]  # 1A intersect #3D
         ]
    X = [x for x in range(3000)
         if 10_000_000 <= (t1 := x * x * x) <= 99_999_999   #12A
         if t1 % 100 >= 10                                  #12A, no zero
         if 100_000 <= (t2 := 1237 * x) <= 999_999                 #5D
         if str(t1)[4] == str(t2)[3]    # 10A intersects 5D
    ]
    Z = [z for z in range(9999)
         if 10_000_000 <= (t := 3 * z * z) <= 99_999_999  #10A
         if t % 10 != 0 ]
    print_start_info(X, Y, Z)

    X = [x for x in X if sum(10 <= f <= 99 for f in factor_list(x)) >= 2]
    Y = [y for y in Y if any(10 <= f <= 99 for f in factor_list(y))]
    Z = [z for z in Z if any(100 <= f <= 999 for f in factor_list(z))]
    print_start_info(X, Y, Z)

    info = [(x, y, z) for x, y, z in itertools.product(X, Y, Z)
            if x + y + 11 <= 999 # 13d
            if 100_000 <= (d4 := 2010 * x + 154 * z) <= 999_999  #4d
            for d3, d5, a1, a10, a12 in [(36 * y, 1237 * x, 6 * y, 3 * z * z, x * x * x)]
            if str(a10)[2:5] == str(d3)[2] + str(d4)[2] + str(d5)[2]
            if str(a12)[2:5] == str(d3)[3] + str(d4)[3] + str(d5)[3]
            if str(a1)[3] == str(d4)[0]
            if str(d5)[4] != '0' and str(d5)[5] != '0'
            # if not print(f'{x=} {y=} {z=} {d3=} {d4=} {d5=} {a1=} {a10=} {a12=}')
            ]
    return info

class Magpie241(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie241()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues)
        self.handle_playground()

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        results = []
        for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd')):
            regexp = r'(\d+).*\((\d)\)'
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(regexp, line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                length = int(match.group(2))
                clue = Clue(f'{number}{letter}', is_across, location, length)
                results.append(clue)
        return results

    def handle_playground(self):
        X, Y, Z = (276, 403, 1964)
        for clue in self._clue_list:
            clue.generator = generators.allvalues

        def is_multiple(x, y):
            self.add_constraint((x, y), lambda x, y: int(x) != int(y) and int(x) % int(y) == 0)

        self.clue_named('1a').generator = generators.known(6 * Y)
        self.clue_named('10a').generator = generators.known(3 * Z * Z)
        self.clue_named('12a').generator = generators.known(X * X * X)
        self.clue_named('3d').generator = generators.known(36 * Y)
        self.clue_named('4d').generator = generators.known(2010 * X + 154 * Z)
        self.clue_named('5d').generator = generators.known(1237 * X)

        self.clue_named('6d').generator = generators.known(*factor_list(X))
        self.clue_named('14d').generator = generators.known(*factor_list(X))
        self.clue_named('15d').generator = generators.known(*factor_list(Y))
        self.clue_named('2d').generator = generators.known(*factor_list(Z))

        self.add_constraint(('5a', '17a'), lambda r, a: int(r) == X + int(a))
        self.add_constraint(('8a', '14d'), lambda r, a: int(r) == 18 * X - int(a))
        is_multiple('9a', '15d')
        self.add_constraint(('14a', '2d', '14d'), lambda r, a, b: int(r) == int(a) + int(b) - X)
        self.add_constraint(('16a', '13d'), lambda r, a: int(r) == Y + int(a))
        self.add_constraint(('17a', '11d', '15d'), lambda r, a, b: int(r) == X + Z + int(a) + int(b))
        self.add_constraint(('18a', '9a', '15d'), lambda r, a, b: int(r) == Y + Z + int(a) + int(b))

        is_multiple('7d', '6d')
        self.add_constraint(('8d', '9a', '6d'), lambda r, a, b: int(r) == X + int(a) + int(b))
        self.add_constraint(('9d', '14d', '6d'), lambda r, a, b: int(r) == int(a) * int(a) * (int(a) + int(b)))
        self.add_constraint(('11d', '6d', '7d', '14d'), lambda r, a, b, c: int(r) == 2 * Y + int(a) + int(b) + int(c))
        self.add_constraint(('13d', '14d'), lambda r, a: int(r) == X + Y + int(a))


    def draw_grid(self, location_to_entry, **args: Unpack[DrawGridArgs]) -> None:
        temp = ["JT", "AKV", "BLW", "CMX", "DNY", "EOZ", "FP", "GQ", "HR", "IS"]
        locations = [(2, i) for i in range(3, 9)] + [(6, i) for i in range(1, 9)]
        values = "DONALDCAMPBELL"
        for loc, val in zip(locations, values):
            assert val in temp[int(location_to_entry[loc])]
            location_to_entry[loc] = val

        X, Y, Z = (276, 403, 1964)
        subtext = f'{X=}, {Y=}, {Z=}'
        super().draw_grid(location_to_entry=location_to_entry,
                          font_multiplier = .8,
                          subtext=subtext,
                          **args)
        # location_to_entry = {loc: temp[int(x)] for loc, x in location_to_entry.items()}
        # super().draw_grid(location_to_entry=location_to_entry,
        #                   font_multiplier = .5, **args)



if __name__ == '__main__':
    Magpie241.run()
    # playground()
