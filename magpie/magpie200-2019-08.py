import itertools
import re
from collections.abc import Sequence

from solver import (
    Clue,
    ClueValue,
    ConstraintSolver,
    generators,
)
from solver.dancing_links import DancingLinks, get_row_column_optional_constraints

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
            clue = Clue(f'{letter}{suffix}', is_across, location, length, context=values)
            clues.append(clue)
    return clues


class MySolver(ConstraintSolver):
    def __init__(self) -> None:
        clue_list = make_clue_list()
        super().__init__(clue_list)

    def solve(self, debug: bool = False) -> None:
        constraints = {}
        optional_constraints = get_row_column_optional_constraints(5, 11)

        for clue in self.clue_list:
            values = clue.context
            min_value, max_value = generators.get_min_max(clue)

            def evaluate(operators: tuple[str, ...], lparen: int, rparen: int) -> tuple[str, int | None]:
                parts = []
                for i in range(5):
                    parts.append('(' if i == lparen else '')
                    parts.append(str(values[i]))
                    parts.append(')' if i == rparen else '')
                    if i < 4:
                        parts.append(operators[i])
                expression = ''.join(parts)
                real_value = eval(expression)
                int_value = int(real_value)
                if min_value <= int_value == real_value < max_value:
                    return expression, int_value
                return expression, None

            def add_constraint(
                value: int, operators: tuple[str, ...], parentheses: tuple[int, int] | None, expression: str,
            ) -> None:
                value_tag = f'Value-{value}'
                operators_tag = ''.join(operators)
                constraint = [f'Clue-{clue.name}', value_tag, operators_tag,
                              *clue.dancing_links_rc_constraints(value),]
                optional_constraints.update((value_tag, operators_tag))
                if parentheses is not None:
                    lparen, rparen = parentheses
                    parentheses_tag = f'Parentheses-{lparen}-{rparen}'
                    constraint.append(parentheses_tag)
                    optional_constraints.add(parentheses_tag)
                constraints[clue, value, operators, parentheses or (-1, -1), expression] = constraint

            for ops in itertools.permutations("+*-/"):
                expression, base_value = evaluate(ops, -1, -1)
                if base_value is not None:
                    add_constraint(base_value, ops, None, expression)
                for start_paren in range(0, 4):
                    for end_paren in range(4, start_paren, -1):
                        expression, value = evaluate(ops, start_paren, end_paren)
                        if value is not None and value != base_value:
                            add_constraint(value, ops, (start_paren, end_paren), expression)

        solver = DancingLinks(constraints, optional_constraints=optional_constraints, row_printer=self.my_row_printer)
        solver.solve(debug=debug)

    def my_row_printer(self, rows: Sequence[tuple[Clue, int, tuple, tuple, str]]) -> None:
        known_values = {clue: str(value)
                        for clue, value, operators, parentheses, expression in rows}
        self.plot_board(known_values)


def run() -> None:
    solver = MySolver()
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
