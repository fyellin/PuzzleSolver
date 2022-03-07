import itertools
import math
import re
from collections import defaultdict
from itertools import permutations
from math import log10
from typing import Any

from solver.draw_grid import draw_grid

MAX_INT = 10_000
MAX_INT_log10 = 4


class MyInt(int):
    def __init__(self, value: int) -> None:
        pass

    def __add__(self, other):
        return MyInt(int(self) + int(other))

    def __sub__(self, other):
        return MyInt(int(self) - int(other))

    def __neg__(self):
        return MyInt(-int(self))

    def __mul__(self, other):
        return MyInt(int(self) * int(other))

    def __truediv__(self, other):
        if int(other) == 0:
            raise ZeroDivisionError
        q, r = divmod(self, other)
        if r == 0:
            return MyInt(q)
        else:
            raise ArithmeticError

    def __pow__(self, power, modulo=None):
        if int(power) < 0:
            raise ArithmeticError
        if log10(self) * power >= MAX_INT_log10:
            raise ArithmeticError
        return MyInt(int(self) ** int(power))

    def __call__(self, *args, **kwargs):
        if 3 <= self <= 10 or self == 0:
            factorial = math.factorial(self)
            if factorial <= MAX_INT:
                return MyInt(factorial)
        raise ArithmeticError


def test_akm():
    count = 0
    values = set(range(1, 10))
    for a, g in itertools.permutations(values, 2):
        if g % a != 0:
            continue
        values2 = values - {a, g}
        for f, h, j, c in itertools.permutations(values2, 4):
            temp1 = (g // a) ** (f + h) - (j * c)
            if not a * 100 + g * 10 <= temp1 <= a * 100 + g * 10 + 9:
                continue
            values3 = values2 - {f, h, j, c}
            for b, d, e in itertools.permutations(values3):
                temp2 = (g + a) * (f + h) + math.factorial(j) + math.factorial(c)
                if not b * 100 + a * 10 <= temp2 <= b * 100 + a * 10 + 9:
                    continue
                temp3 = math.factorial(a) * b + math.factorial(c) - d * e - f
                if not d * 100 + h * 10 <= temp3 <= d * 100 + h * 10 + 9:
                    continue
                print(a, b, c, d, e, f, g, h, j, temp1, temp2, temp3)
                print(f'(\'a\', {(g, a, f, h, j, c)}, {temp1}, "(X/X)^(X+X)-J*C")')
                print(f'(\'k\', {(g, a, f, h, j, c)}, {temp2}, "(X+X)*(X+X)+X!+C!")')
                print(f'(\'m\', {(a, b, c, d, e, f)}, {temp3}, "X!*X+X!-X*E-F")')
                count += 1


"""
4 9 5 3 1 7
8 4 7 2 6 5
2 8 X 6 X X      1 3 9
"""


def test_clue_b():
    good_odds = {482, 571, 573, 579, 163, 169}
    all_values = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5),
                  *((2, 8, a, 6, b, c) for a, b, c in permutations((1, 3, 9)))]
    operations = set(permutations('^^+++'))
    for values in all_values:
        for ops in operations:
            expression = ''.join(f'MyInt({value}) {op} 'for value, op in zip(values, ops))
            expression += f'MyInt({values[-1]})'
            expression = expression.replace('^', '**')
            try:
                result = eval(expression)
                if result in good_odds:
                    exp2 = ''.join(f'X{op}' for op in ops) + 'X'
                    print(f'(\'b\', {values}, {result}, \"{exp2}\")')
            except (SyntaxError, ArithmeticError, ArithmeticError):
                pass


"""
Result is  2 ** 8 + (1 or 9) + 6 ** 3 + (1 or 9)
4 9 5 3 1 7
8 4 7 2 6 5
2 8 X 6 3 X      1  9
"""


def test_clue_c():
    good_odds = {482, 571, 579, 163}
    all_values = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5),
                  (2, 8, 1, 6, 3, 9), (2, 8, 9, 6, 3, 1)]
    operations = set(permutations('-***/'))
    for values in all_values:
        for ops in operations:
            expression = ''.join(f'MyInt({value}) {op} 'for value, op in zip(values, ops))
            expression += f'MyInt({values[-1]})'
            try:
                result = eval(expression)
                if result in good_odds:
                    exp2 = ''.join(f'X{op}' for op in ops) + 'X'
                    print(f'(\'c\', {values}, {result}, \"{exp2}\")')
            except (ArithmeticError, ZeroDivisionError):
                pass


"""
Result is 8 / 4 * 7 * 2 * 6 - 5 = 163.  Don't really learn anything
4 9 5 3 1 7
8 4 7 2 6 5
2 8 X 6 3 X      1  9
"""


def test_clue_n():
    good_evens = {948, 326, 751, 759}
    all_values = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5),
                  (2, 8, 1, 6, 3, 9), (2, 8, 9, 6, 3, 1)]
    operations = set(permutations('+++-*'))
    for original_values in all_values:
        for ops in operations:
            for f_index in range(5):
                values = list(original_values)
                if values[f_index] <= 2:
                    continue
                values[f_index] = math.factorial(values[f_index])
                expression = ''.join(f'MyInt({value}) {op} '
                                     for value, op in zip(values, ops))
                expression += f'MyInt({values[-1]})'
                try:
                    result = eval(expression)
                    if result in good_evens:
                        exp2 = ''.join(f'X{op}' for op in ops) + 'X'
                        exp2 = exp2[0:2*f_index + 1] + "!" + exp2[2*f_index + 1:]
                        print(f'(\'n\', {original_values}, {result}, \"{exp2}\")')
                except (ArithmeticError, SyntaxError):
                    pass


"""
8 + 4 * 7 - 2 + 6! + 5 = 759

4 9 5 3 1 7
8 4 7 2 6 5
2 8 1 6 3 9   
"""


GOOD_EVENS = {948, 326, 759}
GOOD_ODDS = {482, 571, 163}
VALUES = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5), (2, 8, 1, 6, 3, 9)]


def test_clue_p():
    #  Result: 2^8 - 1 + 6! - 3 * 9 = 948
    operations = set(permutations(('+', '-',  '-', '*', '**')))
    for ovalues in VALUES:
        for ops in operations:
            for f_index in range(5):
                values = list(ovalues)
                if values[f_index] <= 2:
                    continue
                values[f_index] = math.factorial(values[f_index])
                expression = ''.join(f'MyInt({value}) {op} '
                                     for value, op in zip(values, ops))
                expression += f'MyInt({values[-1]})'
                try:
                    result = eval(expression)
                    if result in GOOD_EVENS:
                        exp2 = ''.join(f'X{op}' for op in ops) + 'X'
                        exp2 = exp2[0:2*f_index + 1] + "!" + exp2[2*f_index + 1:]
                        print(f'(\'p\', {ovalues}, {result}, \"{exp2}\")')
                except ArithmeticError:
                    pass


def test_expression(letter, expression, parenthesis):
    expression = expression.replace(' ', '').replace('×', '*').replace('–', '-')
    parenthesized_expressions = add_parentheses(expression, parenthesis)
    parses = []
    for pexp in parenthesized_expressions:
        saved_pexp = pexp
        pexp = pexp.replace('!', '()').replace('^', "**")
        for ch in 'abcdef':
            pexp = pexp.replace('X', ch, 1)
        try:
            code = eval(f"lambda a, b, c, d, e, f: {pexp}")
            parses.append((saved_pexp, code))
        except SyntaxError:
            # print("Unable to compile", pexp)
            pass

    expected_values = GOOD_ODDS if letter <= 'j' else GOOD_EVENS
    count = 0
    for values in VALUES:
        xvalues = [MyInt(value) for value in values]
        for pexp, code in parses:
            try:
                result = code(*xvalues)
                if result in expected_values:
                    print(f'(\'{letter}\', {values}, {result}, \"{pexp}\")')
                    count += 1
            except ArithmeticError:
                pass
    assert count > 0


def add_parentheses(expr, parentheses):
    upper = len(expr) + 1
    if parentheses == 1:
        items = [expr[0:left] + '(' + expr[left:right] + ')' + expr[right:]
                 for left in range(0, upper)
                 for right in range(left + 2, upper)]
    elif parentheses == 2:
        items1 = [expr[0:l1] + '(' + expr[l1:l2] + '(' + expr[l2:r2] + ')'
                  + expr[r2:r1] + ')' + expr[r1:]
                  for l1 in range(0, upper) for l2 in range(l1, upper)
                  for r2 in range(l2 + 2, upper) for r1 in range(r2, upper)]
        items2 = [expr[0:l1] + '(' + expr[l1:r1] + ')' + expr[r1:l2] + '('
                  + expr[l2:r2] + ')' + expr[r2:]
                  for l1 in range(0, upper) for r1 in range(l1 + 2, upper)
                  for l2 in range(r1 + 1, upper) for r2 in range(l2 + 2, upper)]
        items = items1 + items2
    else:
        assert False, "Unknown parenthesis size"

    items = [item for item in items
             if ')X' not in item and 'X(' not in item
             if '(X)' not in item and '(X!)' not in item
             if '!(' not in item
             ]
    return items


EQUATIONS = """
d XXX = X + X × X + X + X × X (1)
e XXX = X + X – X – X × X × X (1)
f XXX = X – X + X ! × X + X + X (1)
g XXX = X × X ! × X + X – X – X (1)
h XXX = X × X × X – X ! + X × X (1)
j XXX = X ^ X – X – X × X ! × X (1)
q XXX = – X + X × X × X + X × X (1)
r XXX = X ^ X × X × X – X – X (1)
s XXX = – X – X – X ! + X – X × X (1)
t XXX = X – X + X × X × X – X (2)
u XXX = X / X × X × – X + X ! – X (2)
"""


def run():
    test_akm()
    test_clue_b()
    test_clue_c()
    test_clue_n()
    test_clue_p()

    lines = EQUATIONS.strip().splitlines()
    for line in lines:
        match = re.match(r'([a-z]) XXX = (.*) \((\d)\)', line)
        letter, equation, parens = match.group(1, 2, 3)
        parens = int(parens)
        test_expression(letter, equation, parens)


"""
4 9 5 3 1 7
8 4 7 2 6 5
2 8 1 6 3 9   
"""
CLUES = [
    ('a', (8, 4, 7, 2, 6, 5), 482, "(X/X)^(X+X)-X*X"),
    ('b', (2, 8, 1, 6, 3, 9), 482, "X^X+X+X^X+X"),
    ('c', (8, 4, 7, 2, 6, 5), 163, "X/X*X*X*X-X"),
    ('d', (4, 9, 5, 3, 1, 7), 571, "X+X*(X+X+X)*X"),
    ('e', (2, 8, 1, 6, 3, 9), 163, "X+X-(X-X*X)*X"),
    ('f', (4, 9, 5, 3, 1, 7), 482, "X-X+X!*(X+X)+X"),
    ('g', (8, 4, 7, 2, 6, 5), 571, "X*X!*(X+X-X)-X"),
    ('h', (4, 9, 5, 3, 1, 7), 163, "X*(X*X-X!)+X*X"),
    ('j', (2, 8, 1, 6, 3, 9), 571, "X^X-(X-X*X!)*X"),

    ('k', (8, 4, 7, 2, 6, 5), 948, "(X+X)*(X+X)+X!+X!"),
    ('m', (4, 9, 5, 3, 1, 7), 326, "X!*X+X!-X*X-X"),
    ('n', (8, 4, 7, 2, 6, 5), 759, "X+X*X-X+X!+X"),
    ('p', (2, 8, 1, 6, 3, 9), 948, "X^X-X+X!-X*X"),
    ('q', (4, 9, 5, 3, 1, 7), 948, "-X+(X*X*X+X)*X"),
    ('r', (2, 8, 1, 6, 3, 9), 759, "X^X*X*(X-X)-X"),
    ('s', (4, 9, 5, 3, 1, 7), 759, "-X-(X-X!+X-X)*X"),
    ('t', (2, 8, 1, 6, 3, 9), 326, "X-(X+X)*X*(X-X)"),
    ('u', (8, 4, 7, 2, 6, 5), 326, "X/X*(X*(-X+X)!-X)"),
]


def verify_clues():
    for (letter, values, result, expression) in CLUES:
        for value in values:
            expression = expression.replace('X', f'MyInt({value})', 1)
        expression = expression.replace('^', '**').replace('!', '()')
        assert result == eval(expression)


def my_draw_grid():
    grid = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5), (2, 8, 1, 6, 3, 9)]
    columns = [a * 100 + b * 10 + c for a, b, c in zip(*grid)]
    location_to_clue_numbers = defaultdict(list)
    location_to_entry = {}
    for (letter, values, result, _) in CLUES:
        row = grid.index(values) + 1
        column = columns.index(result) * 2 + 2
        location_to_clue_numbers[(row, column)].append(letter)
    for row, values in enumerate(grid):
        for column, value in enumerate(values):
            location_to_entry[row + 1, column * 2 + 2] = str(value)

    for (letter, values, _, code) in CLUES[-3:]:
        row = grid.index(values) + 1
        code = code.replace('*', '×').replace('-', '–')
        for column, val in enumerate(code.split('X')):
            location_to_entry[row, column * 2 + 1] = val

    def grid_drawer(_plt, axes):
        for col in range(2, 14):
            axes.plot([col, col], [1, 4], 'black', linewidth=3)
        for col in range(2, 14, 2):
            for row in range(1, 5):
                axes.plot([col, col + 1], [row, row], 'black', lw=3)

    draw_grid(max_row=4, max_column=14,
              clued_locations={(r, c)
                               for r, c in itertools.product(range(1, 4), range(1, 14))},
              location_to_entry=location_to_entry,
              location_to_clue_numbers=location_to_clue_numbers,
              font_multiplier=.7,
              grid_drawer=grid_drawer
              )


if __name__ == '__main__':
    my_draw_grid()
