import itertools
import math
import re
from collections import defaultdict
from itertools import permutations
from math import log10

from solver import Clue
from solver.draw_grid import draw_grid
from solver.equation_parser import EquationParser

MAX_INT = 10_000
MAX_INT_log10 = 4

def my_div(a, b):
    if b == 0:
        raise ZeroDivisionError
    q, r = divmod(a, b)
    if r == 0:
        return q
    raise ArithmeticError

def my_pow(base, power):
    if power < 0:
        raise ArithmeticError
    if log10(base) * power >= MAX_INT_log10:
        raise ArithmeticError
    return base ** power

def my_fact(x):
    if 3 <= x <= 10 or x == 0:
        factorial = math.factorial(x)
        if factorial <= MAX_INT:
            return factorial
    raise ArithmeticError

EQUATION_PARSER = EquationParser()
MAPPING = dict(div=my_div, pow=my_pow, fact=my_fact)


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

def test_specific(clue, good_results, all_values, operators, use_factorial=False):
    for op1, op2, op3, op4, op5 in set(permutations(operators)):
        expression = f'u{op1}v{op2}w{op3}x{op4}y{op5}z'
        evaluator = Clue.create_callable(expression, MAPPING)
        if not use_factorial:
            for values in all_values:
                try:
                    result = evaluator(*values)
                    if result in good_results:
                        expression2 = re.sub(r'[uvwxyz]', 'X', expression)
                        print(f'(\'{clue}\', {values}, {result}, \"{expression2}\")')
                except ArithmeticError:
                    pass
        else:
            for original_values in all_values:
                for f_index, f_var in enumerate('uvwxyz'):
                    values = list(original_values)
                    if values[f_index] <= 2:
                        continue
                    values[f_index] = math.factorial(values[f_index])
                    try:
                        result = evaluator(*values)
                        if result in good_results:
                            expression2 = expression.replace(f_var, f_var + "!")
                            expression2 = re.sub(r'[uvwxyz]', 'X', expression2)
                            print(
                                f'(\'p\', {original_values}, {result}, \"{expression2}\")')
                    except ArithmeticError:
                        pass


def test_clue_b():
    good_odds = {482, 571, 573, 579, 163, 169}
    all_values = [(4, 9, 5, 3, 1, 7), (8, 4, 7, 2, 6, 5),
                  *((2, 8, a, 6, b, c) for a, b, c in permutations((1, 3, 9)))]
    test_specific('b', good_odds, all_values, '^^+++')


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
    test_specific('c', good_odds, all_values, '-***/')


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
    test_specific('n', good_evens, all_values, '+++-*', use_factorial=True)


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
    test_specific('p', GOOD_EVENS, VALUES, '+--*^', use_factorial=True)


def test_expression(letter, expression, parenthesis):
    mapping = dict(div=my_div, pow=my_pow, fact=my_fact)
    expression = expression.replace(' ', '')
    for ch in 'uvwxyz':
        expression = expression.replace('X', ch, 1)
    parenthesized_expressions = add_parentheses(expression, parenthesis)
    parses = []
    for pexp in parenthesized_expressions:
        try:
            evaluator = Clue.create_callable(pexp, mapping)
            parses.append((pexp, evaluator))
        except SyntaxError:
            pass

    expected_values = GOOD_ODDS if letter <= 'j' else GOOD_EVENS
    count = 0
    for values in VALUES:
        for pexp, evaluator in parses:
            try:
                result = evaluator(*values)
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
    for (letter, values, expected_result, expression) in CLUES:
        for value in values:
            expression = expression.replace('X', f'{value}', 1)
        evaluator = Clue.create_callable(expression, MAPPING)
        result = evaluator()
        assert expected_result == result


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
    # verify_clues()
    run()
    my_draw_grid()
