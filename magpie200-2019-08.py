import itertools
import re
from typing import Iterable, Sequence, Optional, Tuple

import Generators
from Clue import ClueValueGenerator, Clue, ClueList
from GenericSolver import SolverByClue

ACROSS = """
a 159 56 165 67 5      4
d 161 114 168 12 29    4
f 35 48 72 51 160      3
h 79 99 162 18 16      4
i 86 40 154 22 196     4
m 135 9 54 122 41      3
p 154 8 52 46 100      3
q 49 166 45 24 180     3
r 50 92 57 144 36      4
s 182 14 10 76 115     4
u 184 30 42 140 156    3
v 147 199 7 32 150     4
w 189 27 107 31 110    4
"""

DOWN = """
a 126 58 113 87 3      5
b 187 4 39 132 44      2
c 94 138 53 177 59     5
d 73 28 198 33 142     5
e 55 102 34 131 119    5
f 117 188 47 93 20     5
g 97 172 43 130 21     5
k 61 91 23 15 2        2
n 98 1 38 152 60       2
t 175 25 6 17 141      2
"""

MAP = """
abc.d.e.f.g
..h...ik...
m..np...q..
.r...s...t.
u..v...w...
"""

def generator(values: Sequence[int]) -> ClueValueGenerator:
    def result(clue: Clue) -> Iterable[int]:
        min_value, max_value = Generators.get_min_max(clue)
        for op1, op2, op3, op4 in itertools.permutations("+*-/"):
            def get_value(lparen:int, rparen:int) -> Tuple[str, Optional[int]]:
                def q(i: int) -> str:
                    return f"{'(' if i == lparen else ''}{values[i - 1]}{')' if i == rparen else ''}"
                expression = f"{q(1)} {op1} {q(2)} {op2} {q(3)} {op3} {q(4)} {op4} {q(5)}"
                real_value = eval(expression)
                value = int(real_value)
                return expression, (value if (value == real_value and min_value <= value < max_value) else None)
            expression, base_value = get_value(-1, -1)
            if base_value:
                yield base_value
                print(f'{clue.name}     {base_value:>5} "{expression}"')
            for start_paren in range(1, 5):
                for end_paren in range(5, start_paren, -1):
                    expression, value = get_value(start_paren, end_paren)
                    if value and value != base_value:
                        print(f'{clue.name} {start_paren} {end_paren} {value:>5} "{expression}"')
                        yield value
        print()

    return result


def make_clue_list() -> ClueList:
    locations = {}
    for row, line in enumerate(MAP.split()):
        for column, item in enumerate(line):
            if item != '.':
                locations[item] = row + 1, column + 1
    clues = []
    for is_across, suffix, clue_info in ((True, 'a', ACROSS), (False, 'd', DOWN)):
        for line in clue_info.split('\n'):
            if not line:
                continue
            match = re.fullmatch(r'([a-z])\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*', line)
            assert match
            letter = match.group(1)
            values = [int(match.group(i))for i in range(2,7)]
            length = int(match.group(7))
            location = locations[letter]
            clue = Clue(f'{letter}{suffix}', is_across, location, length, generator=generator(values))
            clues.append(clue)
    clue_list = ClueList(clues)
    return clue_list


class MySolver(SolverByClue):
    pass


def run() -> None:
    clue_list = make_clue_list()
    clue_list.verify_is_180_symmetric()
    solver = MySolver(clue_list)
    solver.solve(debug=False)


if __name__ == '__main__':
    run()


"""


<Clue aa> 1 5 2314 (159-56+165*67/5)
<Clue da> 1 5 1728 (161+114*168/12-29)
<Clue fa> 1 5 161 (35-48/72*51+160)
<Clue ha> 1 5 7814 (79*99+162/18-16)
<Clue ia> 1 5 1418 (86-40+154/22*196)
<Clue ma> 1 5 729 (135/9*54-122+41)
<Clue pa> 1 5 947 (154/8*52+46-100)
<Clue qa> 1 5 209 (49+166-45*24/180)
<Clue ra> 1 5 4547 (50*92-57+144/36)
<Clue sa> 1 5 8743 (182/14-10+76*115)
<Clue ua> 1 5 331 (184-30*42/140+156)
<Clue va> 1 5 4297 (147*199/7-32+150)
<Clue wa> 3 4 8367 189/27+(107-31)*110

<Clue ad> 1 2 20763 (126+58)*113-87/3
<Clue bd> 1 5 34    (187-4*39+132/44)
<Clue cd> 2 3 17951   94*(138+53)-177/59
<Clue dd> 2 5 11972  73*(28-198/33+142)
<Clue ed> 1 4 21777 (55-102/34+131)*119
<Clue fd> 1 3 11233 (117+188/47)*93-20
<Clue gd> 2 4 12977  97*(172/43+130)-21
<Clue kd> 3 5 48     61+91/(23-15*2)
<Clue nd> 1 5 84    (98+1-38/152*60)
<Clue td> 1 5 46    (175/25-6*17+141)

13 14 34 35 23 24 25
"""
