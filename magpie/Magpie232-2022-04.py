import itertools
import math
import re
from collections import defaultdict
from typing import Any

from solver import Clue, Clues, ConstraintSolver

CLUES = """
3d A * R * A * B * L * E [3]
4d P * L * O * U/(G/H)  [3]
5d O * (V - U) * M [3]
6a (M + A) * P * L * E [4]
12d Q+U+I+D [3]
7a J * (E+E)-R [4]
9a J * E * L * L * Y - P *(E+A+R) [5]
8d (S+H)**(O+O) +T [3]
15a E+(X+E) * R * C * I * S * E + S [3]
11d A + (N* X+I+E*T)Y [3]
12a M * I * (X - E) * D [4]
2d -(V-I)**C *  (T+O) + (R+Y)! [3]
1a (Y+E) * L * L + V**(I+O+L) [3]
13d (D + R)**(U*G) * (A*B)**(B(R + E) - V) [3]
14a (W-R)**Y + (N + E + C)/K [4]
"""

TABLES3 = None
TABLES4 = None
TABLES5 = None


def build_tables():
    global TABLES3, TABLES4, TABLES5
    TABLES3 = defaultdict(list)
    TABLES4 = defaultdict(list)
    TABLES5 = defaultdict(list)
    for a, b, c in itertools.product(range(1, 11), repeat=3):
        value = a * a + b * b + c * c
        if 10 <= value < 100:
            TABLES3[value].append(100 * a + 10 * b + c)
    for a, b, c, d in itertools.product(range(1, 11), repeat=4):
        value = a * a + b * b + c * c + d * d
        if 10 <= value < 100:
            TABLES4[value].append(1000 * a + 100 * b + 10 * c + d)
    for a, b, c, d, e in itertools.product(range(1, 11), repeat=5):
        value = a * a + b * b + c * c + d * d + e * e
        if 10 <= value < 100:
            TABLES5[value].append(10000 * a + 1000 * b + 100 * c + 10 * d + e)


def parse_clues():
    clues = {}
    for line in CLUES.strip().splitlines():
        match = re.match(r'([1-9]+[ad]) (.*) \[([345])\]', line.strip())
        clues[match.group(1)] = match.group(2), int(match.group(3))
    return clues


def get_order():
    clues = parse_clues()
    table = {clue: {x for x in equation if x.isalpha()}
             for clue, (equation, _length) in clues.items()}
    seen = table.pop('3d') | table.pop('4d') | table.pop('5d')
    for letters in table.values():
        letters -= seen
    while table:
        smallest = min(table, key=lambda x: len(table[x]))
        seen = table.pop(smallest)
        print(smallest, seen)
        for letters in table.values():
            letters -= seen


def get_values():
    if TABLES3 is None:
        build_tables()

    def pull(result, letters):
        return [[result[letter] for letter in letters]]

    results = [dict(a=a, r=r, b=b, l=l, e=e, d3=3)
               for a, r, b, l, e in itertools.product(range(1, 4), repeat=5)
               if a * r * a * b * l * e == 3]

    results = [result | dict(p=p, o=o, u=u, g=g, h=h, d4=6)
               for result in results
               for l, in pull(result, "l")
               for p, o, u, g, h in itertools.product(range(1, 7), repeat=5)
               if h != 1 and g != h
               if p * l * o * u / (g / h) == 6]

    results = [result | dict(v=v, u=u, m=m, d5=9, a6=a6)
               for result in results
               for o, a, p, l, e in pull(result, "oaple")
               for v, u, m in itertools.product(range(1, 11), repeat=3)
               if o * (v - u) * m == 9
               if (a6 := (m + a) * p * l * e) in TABLES4
               ]

    results = [result | dict(j=j, a7=a7)
               for result in results
               for e, r in pull(result, "er")
               for j in range(1, 11)
               if (a7 := j * (e + e) - r) in TABLES4
               if result['a6'] < a7]

    results = [result | dict(y=y, a9=a9)
               for result in results
               for j, e, l, p, a, r in pull(result, "jelpar")
               for y in range(1, 11)
               if (a9 := (j * e * l * l * y - p * (e + a + r))) in TABLES5
               if result['a7'] < a9]

    results = [result | dict(i=i, a1=a1)
               for result in results
               for y, e, l, v, o in pull(result, "yelvo")
               for i in range(1, 11)
               if (a1 := (y + e) * l * l + v ** (i + o + l)) in TABLES3
               if result['a9'] < a1]

    results = [result | dict(d=d, d13=d13)
               for result in results
               for r, u, g, a, b, v, e in pull(result, "rugabve")
               for d in range(1, 11)
               if (d13 := (d + r)**(u * g) * (a * b) ** (b * (r + e) - v)) in TABLES3
               if result['a1'] < d13]

    results = [result | dict(q=q, d12=d12)
               for result in results
               for u, i, d in pull(result, "uid")
               for q in range(1, 11)
               if (d12 := q + u + i + d) in TABLES3
               if result['a6'] < d12 < result['a7']]

    results = [result | dict(x=x, a12=a12, d10=a12)
               for result in results
               for m, i, e, d in pull(result, "mied")
               for x in range(1, 11)
               if (a12 := m * i * (x - e) * d) in TABLES4
               if a12 in TABLES3  # 10d = 12a, so must be in both tables
               if result['a9'] < a12 < result['a1']]

    results = [result | dict(s=s, t=t, d8=d8)
               for result in results
               for h, o in pull(result, "ho")
               for s in range(1, 11) for t in range(1, 11)
               if (d8 := (s + h) ** (o + o) + t) in TABLES3
               if result['a9'] < d8 < result['a12']]

    results = [result | dict(c=c, a15=a15)
               for result in results
               for e, x, r, i, s in pull(result, "exris")
               for c in range(1, 11)
               if (a15 := e + (x + e) * r * c * i * s * e + s) in TABLES3
               if result['d8'] < a15 < result['a12']]

    results = [result | dict(d2=d2)
               for result in results
               for v, i, c, t, o, r, y in pull(result, "victory")
               if (d2 := -(v - i) ** c * (t + o) + math.factorial(r + y)) in TABLES3
               if result['a12'] < d2 < result['a1']]

    results = [result | dict(n=n, d11=d11)
               for result in results
               for a, x, i, e, t, y in pull(result, "axiety")
               for n in range(1, 11)
               if (d11 := (a + (n * x + i + e * t) * y)) in TABLES3
               if result['a15'] < d11 < result['a12']]

    results = [result | dict(k=k, w=w, a14=int(a14))
               for result in results
               for r, y, n, e, c, in pull(result, "rynec")
               for k in range(1, 11) for w in range(1, 11)
               if (a14 := (w - r) ** y + (n + e + c) / k) in TABLES4
               if a14 == int(a14)
               if k != 1
               if a14 > result['d13']
               ]
    return results


GRID = """
XX.XX
XX...
X.X..
X...X
XX.X.
X....
..X..
"""


class Magpie231Solver(ConstraintSolver):
    @staticmethod
    def run(result):
        solver = Magpie231Solver(result)
        # solver.plot_board({})
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self, result):
        self.result = result
        if TABLES3 is None:
            build_tables()
        clues = self.get_clues()
        super().__init__(clues)
        self.add_all_constraints()

    def get_clues(self) -> list[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for line in CLUES.strip().splitlines():
            match = re.match(r'([1-9]+)([ad]) .* \[([345])\]', line.strip())
            number, is_across, length = match.groups()
            number, length = int(number), int(length)
            clue = Clue(f'{number}{is_across}', is_across == 'a',
                        grid[number - 1], length, generator=self.generator)
            clues.append(clue)
        clues.append(Clue('10d', False, grid[10 - 1], 3, generator=self.generator))
        return clues

    def add_all_constraints(self):
        clues = ('3d', '4d', '5d', '13d', '15a', '1a', '12d', '8d', '11d', '2d', '6a',
                 '7a', '12a', '14a', '9a')
        for i, j in itertools.combinations(clues, 2):
            self.add_constraint((i, j), lambda x, y: int(x) < int(y))

    def generator(self, clue: Clue):
        length = clue.length
        key = clue.name[-1] + clue.name[:-1]
        table = TABLES3 if length == 3 else TABLES4 if length == 4 else TABLES5
        value = self.result[key]
        if value < 10:
            result = {3: [111], 6: [112, 121, 211], 9: [122, 212, 122]}[value]
        else:
            result = table[value]
        return result

    def draw_grid(self, *, location_to_entry, **args: Any) -> None:
        mapper = defaultdict(list)
        for letter in "abcdeghijklmnopqrstuvwxy":
            mapper[self.result[letter]].append(letter.upper())
        print(''.join(mapper[1]))
        mapper[1] = '*',
        location_to_entry = {location: ''.join(mapper[int(digit)])
                                 for location, digit in location_to_entry.items()}
        super().draw_grid(location_to_entry=location_to_entry, **args)


def go():
    results = get_values()
    for result in results:
        Magpie231Solver.run(result)


if __name__ == '__main__':
    go()
