import itertools
import re
from typing import Iterable, Sequence, Optional, Tuple, Dict, cast, Any

from solver import Clue, ClueValueGenerator, ClueValue, ConstraintSolver
from solver import generators

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


class MyString(str):
    def __repr__(self) -> str:
        return '<' + str(self) + '>'

    def __new__(cls, value: int, operators: Tuple[str, ...], parentheses: Optional[Tuple[int, int]], expression: str
                ) -> Any:
        return super().__new__(cls, value)  # type: ignore

    def __init__(self, _value: int, operators: Tuple[str, ...], parentheses: Optional[Tuple[int, int]], expression: str
                 ) -> None:
        super().__init__()
        self.operators = operators
        self.parentheses = parentheses
        self.expression = expression


def generator(values: Sequence[int]) -> ClueValueGenerator:
    def result(clue: Clue) -> Iterable[MyString]:
        min_value, max_value = generators.get_min_max(clue)
        for ops in itertools.permutations("+*-/"):
            def get_value(lparen: int, rparen: int) -> Tuple[str, Optional[int]]:
                def q(i: int) -> str:
                    return f"{'(' if i == lparen else ''}{values[i]}{')' if i == rparen else ''}"
                equation = f"{q(0)} {ops[0]} {q(1)} {ops[1]} {q(2)} {ops[2]} {q(3)} {ops[3]} {q(4)}"
                real_value = eval(equation)
                int_value = int(real_value)
                if int_value == real_value and min_value <= int_value < max_value:
                    return equation, int_value
                else:
                    return equation, None
            expression, base_value = get_value(-1, -1)
            if base_value:
                yield MyString(base_value, ops, None, expression)
            for start_paren in range(0, 4):
                for end_paren in range(4, start_paren, -1):
                    expression, value = get_value(start_paren, end_paren)
                    if value and value != base_value:
                        yield MyString(value, ops, (start_paren, end_paren), expression)
    return result


def make_clue_list() -> Sequence[Clue]:
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
            values = [int(match.group(i))for i in range(2, 7)]
            length = int(match.group(7))
            location = locations[letter]
            clue = Clue(f'{letter}{suffix}', is_across, location, length, generator=generator(values))
            clues.append(clue)
    return clues


class MySolver(ConstraintSolver):
    def __init__(self, clue_list: Sequence[Clue]) -> None:
        super().__init__(clue_list)
        for clue1, clue2 in itertools.combinations(clue_list, 2):
            self.add_constraint((clue1, clue2), MySolver.must_be_different)

    @staticmethod
    def must_be_different(aa: ClueValue, bb: ClueValue) -> bool:
        a = cast(MyString, aa)
        b = cast(MyString, bb)
        if a.operators == b.operators:
            return False
        if a.parentheses and a.parentheses == b.parentheses:
            return False
        return True

    def show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        super().show_solution(known_clues)
        for clue in self._clue_list:
            value = cast(MyString, known_clues[clue])
            print(f'{clue.name} {value:<5} = {value.expression}')


def run() -> None:
    clue_list = make_clue_list()
    solver = MySolver(clue_list)
    solver.verify_is_180_symmetric()
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
