import itertools
import re
from pathlib import Path
from typing import Any, Iterable

import math

from solver import Clue, ClueValue, Clues, Evaluator, Location, \
    MultiEquationSolver, KnownClueDict, KnownLetterDict

GRID = """
XXXXX.XX
X..X....
XX...X.X
X.....X.
.......X
XXXX.XX.
X.X...X.
X...X...
"""

LINES = """
1a CRA + Z – YB + IR – D  (2)
24a WI**(Z + A) – RD      (3)
17a SQUE + AK – Y         (3)
12a W+H**I +R+L–W**I +ND    (3)
14a THE + L(I + O) – N    (2)
23a SU!/P+E(R–M–E–X)      (2)
27a (BI + G)(E/A)SY       (4)
3a (I + C + EM)A + N      (2)
6a BUL + L + D + O – G    (2)
5a B+I+LL(Y–W–H)–I**(ZZ)      (2)
26a WA! – RR + I – OR     (2)
8a THE + P((O + W)E + R)  (3)
9a WILD + T + H(IN – G)   (4)
20a Q(U – E/E)N – (V – E)E (3)
15a BOO – M + B + OO – M   (2)
10a B – I(G + DA/D) + D!Y  (3)
25a LAST - 32              (2)
v (V – I – K + IN)G 11d    (3)
v THE + JUD + GE 13d       (2)
v THE + B + E + AST 16d    (3)
v – W – (O – L – F)IE 2d   (2)
v DR/I – RO + NF(I + S) – T 3d (3)
v THE + (M – A + C)H – I – N + E 14d  (3)
v M + A + G**I – CI + A + N 19d  (3)
v – N + U + GGE + T 15d        (2)
v – T + ER + M – I + NAT + O + R 7d  (2)
v J – A + CK + P**O + T 22d  (3)
v ICE + M(A + I) + DEN 5d  (3)
v SP**A + C + E(MA + N) 20d  (3)
v P**I(TB + U + L) + L 21d   (3)
v THE+G–R–E/A+(T+E)(S+T) 23d  (2)
v THE + H + AWK 4d  (3)
v – A(S + S) + (ASS)!I – N 18d  (2)
v 0 6d (3)
"""

SOLUTION = {'18d': '㉑⑳', '25a': '㉒⑱', '16d': '19⑱', '14a': '㉑㉒', '15a': '⑳㉑',
            '14d': '㉑51', '3a': '⑳⑳', '19d': '22⑫', '15d': '⑳㉒', '27a': '2196',
            '21d': '2⑳1', '20d': '㉒89', '10a': '㉑19', '5d': '㉕26', '6a': '㉘㉘',
            '7d': '㉘⑫', '23d': '㉒㉒', '23a': '㉒⑳', '3d': '⑳29', '26a': '㉒⑪',
            '8a': '2⑳2', '2d': '⑫⑳', '9a': '2225', '12a': '11㉖', '13d': '㉖㉑',
            '24a': '28⑪', '1a': '⑲⑫', '5a': '㉕⑱', '22d': '2㉒9', '4d': '⑳26',
            '17a': '1㉑2', '20a': '㉒32', '11d': '1㉒2'}

LETTERS = (6, 16, 17, 5, 12, 20, 13, 10, 3, 19, 9, 25, 26, 28, 11, 2,
           14, 21, 1, 15, 7, 22, 4,  8, 18, 0)


class Magpie260 (MultiEquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False, multiprocessing=False, max_debug_depth=2)

    @classmethod
    def run2(cls):
        solver = cls()
        solver.part2()

    @classmethod
    def run3(cls):
        solver = cls()
        solver.part3()

    def __init__(self) -> None:
        self.triples2, self.triples3, self.triples4 = make_triples()
        clues = self.get_clues()
        self.doubles = {location for clue in clues if clue.length == 2
                        for location in clue.locations}
        super().__init__(clues, items=range(0, 29))
        self.clue_named("18d").priority = 1

    def get_allowed_regexp(self, location: Location) -> str:
        if location in self.doubles:
            return '[^0-9]'
        return super().get_allowed_regexp(location)

    def get_clues(self):
        result: list[Clue] = []
        locations = Clues.get_locations_from_grid(GRID)
        for line in LINES.splitlines():
            line = line.strip()
            if not line:
                continue
            if line[0] != 'v':
                match = re.fullmatch(r'(\d+)(a)\s(.*)\s+\((\d+)\)\s*', line)
                if not match:
                    raise ValueError(f'Cannot create a match from "{line}"')
                number, letter, expression, length = match.group(1, 2, 3, 4)
                is_across = True
            else:
                match = re.fullmatch(r'v\s+(.*)\s+(\d+)(d)\s+\((\d+)\)\s*', line)
                if not match:
                    raise ValueError(f'Cannot create a match from "{line}"')
                expression, number, letter, length = match.group(1, 2, 3, 4)
                is_across = False
            number = int(number)
            location = locations[number - 1]
            clue = Clue(f'{number}{letter}', is_across, location, int(length))
            if expression != '0':
                encoder = [self.triples2, self.triples3, self.triples4][int(length) - 2]
                mapping = {"fact": factorial}
                clue.evaluators = Evaluator.create_evaluators(
                    expression, wrapper=make_wrapper(encoder), mapping=mapping)
            result.append(clue)
        return result

    def check_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> bool:
        temp = {clue.name: value for clue, value in known_clues.items()}
        print(temp)
        return super().check_solution(known_clues, known_letters)

    def draw_gridx(self, location_to_entry, clued_locations, **args: Any) -> None:
        location_to_entry = {location: str(ALPHABET.index(value))
                                           for location, value in location_to_entry.items()}
        clued_locations = set(itertools.product(range(1, 9), repeat=2))
        location_to_entry[4, 3] = '2'
        location_to_entry[4, 4] = location_to_entry[4, 5] = '0'
        location_to_entry[4, 6] = '1'
        location_to_entry[5, 3] = '1'
        location_to_entry[5, 4] = '9'
        location_to_entry[5, 5] = '7'
        location_to_entry[5, 6] = '8'

        super().draw_grid(location_to_entry=location_to_entry,
                          extra=self.extra,
                          clued_locations={}, **args)

    def extra(self, plt, axes):
        import matplotlib.font_manager as fm
        path = Path(__file__).parent.parent / "misc" / "Digital-7.mono.ttf"
        font_prop = fm.FontProperties(fname=path)

    def part2(self):
        info = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",
                        (6, 16, 17, 5, 12, 20, 13, 10, 3, 19, 9, 25, 26, 28, 11, 2, 14, 21, 1, 15, 7, 22, 4, 8, 18, 0)))
        pairs = {clue: int(clue.evaluators[0].raw_call(info)) for clue in self._clue_list if clue.evaluators}
        lefts, rights = [], []
        for i in range(16):
            clueA, clueB = self._clue_list[i], self._clue_list[i + 17]
            resultA, resultB = pairs[clueA], pairs[clueB]
            print(f'{clueA.name:3} {clueB.name:3} {resultA} {resultB} {"*" if resultA > resultB else ""}')
            if resultA > resultB:
                lefts.append(resultA)
            else:
                rights.append(resultB)
        print(lefts, rights)
        def match_up(winner, loser):
            temp = winner + 32 * (1 - (1 / (1 + 10 ** ((loser - winner) / 400))))
            return int(math.ceil(temp))

        while len(lefts) > 1:
            lefts = [match_up(lefts[i], lefts[i + 1]) for i in range(0, len(lefts), 2)]
            rights = [match_up(rights[i], rights[i + 1]) for i in range(0, len(rights), 2)]
            print(lefts, rights)

    def part3(self):
        clue_values = {self.clue_named(name): value for name, value in SOLUTION.items()}
        self.plot_board(clue_values)

    def draw_grid(self, location_to_entry, clued_locations, left_bars, top_bars, **args: Any) -> None:
        reverse_info = dict(zip(LETTERS, "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        clued_locations = set(itertools.product(range(1, 9), repeat=2))
        center_locations = list(itertools.product((4, 5), range(3, 7)))
        location_to_entry.update(zip(center_locations, "20011978"))
        location_to_entry = {location: str(ALPHABET.index(value))
                             for location, value in location_to_entry.items()}
        for location in {(1, x) for x in range(1, 9)} | {(x, 8) for x in range(1, 8)}:
            old_value = location_to_entry[location]
            location_to_entry[location] = reverse_info[int(old_value)]
        for location in {(8, x) for x in range(1, 9)} | {(x, 1) for x in range(2, 9)}:
            old_value = location_to_entry[location].replace('6', 'x').replace('9', '6').replace('x', '9')
            location_to_entry[location] = reverse_info[int(old_value[::-1])]
        left_bars -= set(itertools.product((4, 5), (4, 5, 6)))
        top_bars -= {(5, i) for i in (3, 4, 5, 6)}
        shading = {(row, column): 'blue' for row in (3, 4) for column in (3, 4, 5, 6)}
        super().draw_grid(location_to_entry={},
                          extra=lambda plt, axes:
                              self.extra(plt, axes, location_to_entry),
                          left_bars = left_bars,
                          top_bars = top_bars,
                          shading=shading,
                          subtext = 'KASPAROV ELO 2851',
                          clued_locations=clued_locations, **args)

    def extra(self, plt, axes, location_to_entry):
        import matplotlib.font_manager as fm
        path = Path(__file__).parent.parent / "misc" / "Digital-7.mono.ttf"
        font_prop = fm.FontProperties(fname=path)
        for (row, column), entry in location_to_entry.items():
            rotation = 0
            fontproperties = None
            if row == 8 or (column == 1 and row != 1):
                rotation = 180
            if row not in (1, 8) and column not in (1, 8):
                fontproperties = font_prop
            axes.text(column + 1 / 2, row + 1 / 2, entry,
                      color='black',
                      fontsize=30, fontweight='bold',
                      fontfamily="SF Pro Text",
                      fontproperties=fontproperties,
                      rotation=rotation,
                      va='center', ha='center')



ALPHABET = "0123456789⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳㉑㉒㉓㉔㉕㉖㉗㉘"

def make_triples():
    triples2 = {}
    triples3 = {}
    triples4 = {}
    for i in range(1000, 10000):
        triples4[i] = str(i),

        q, r, = divmod(i, 100)
        if 10 <= q <= 28 and 10 <= r <= 28:
            triples2[i] = (ALPHABET[q] + ALPHABET[r]),
        threes = []
        d1, d2, d3, d4 = str(i)
        if 10 <= int(d1 + d2) <= 28:
            threes.append(ALPHABET[int(d1  +d2)] + d3 + d4)
        if 10 <= int(d2 + d3) <= 28:
            threes.append(d1 + ALPHABET[int(d2 + d3 )] + d4)
        if 10 <= int(d3 + d4) <= 28:
            threes.append(d1 + d2 + ALPHABET[int(d3 + d4)])
        if threes:
            triples3[i] = threes
    return triples2, triples3, triples4

def factorial(x):
    if x < 0 or x > 10 or int(x) != x:
        raise ArithmeticError
    return math.factorial(x)

def make_wrapper(encoder):
    def wrapper(evaluator, value_dict: dict[str, int]) -> Iterable[ClueValue]:
        try:
            result = evaluator.raw_call(value_dict)
            int_result = int(result)
            if result == int_result > 0:
                return encoder.get(result, ())
        except ArithmeticError:
            pass
        return ()
    return wrapper

if __name__ == '__main__':
    Magpie260.run()
