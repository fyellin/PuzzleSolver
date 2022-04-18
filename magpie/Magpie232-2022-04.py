import fractions
import itertools
import operator
import re
from collections import defaultdict
from datetime import datetime
from typing import Any

from solver import Clue, Clues, ConstraintSolver, Evaluator

CLUES = """
3d ARABLE [3]
4d PLOU/(G/H) [3]
5d O(V – U)M [3]
6a (M + A)PLE [4]
12d Q+U+I+D [3]
7a J(E+E)–R [4]
9a JELLY–P(E+A+R) [5]
8d (S+H)^(O+O) +T [3]
15a E+(X+E)RCISE+S [3]
11d A+(NX+I+ET)Y [3]
12a MI(X – E)D [4]
2d –(V–I)^C(T+O)+(R+Y)! [3]
1a (Y+E)LL+V^(I+O+L) [3]
13d (D + R)^(UG)(AB)^(B(R + E) – V) [3]
14a (W–R)^Y +(N+E+C)/K [4]
"""

GRID = """
XX.XX
XX...
X.X..
X...X
XX.X.
X....
..X..
"""

TABLES3 = None
TABLES4 = None
TABLES5 = None


def build_tables():
    global TABLES3, TABLES4, TABLES5
    if TABLES3 is not None:
        return
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

def my_div(a, b):
    if b == 0 or b == 1:
        raise ZeroDivisionError
    return fractions.Fraction(a, b)

def my_pow(a, b):
    if a == 1 or b == 1:
        raise ZeroDivisionError
    return operator.__pow__(a, b)

def parse_clues(*, use_10d: bool = False):
    clues = []
    grid = Clues.get_locations_from_grid(GRID)
    for line in CLUES.strip().splitlines():
        match = re.match(r'([1-9]+)([ad]) (.*) \[([345])\]', line.strip())
        number, letter, equation, length = match.group(1, 2, 3, 4)
        clue = Clue(f'{number}{letter}', letter == 'a',
                    base_location=grid[int(number) - 1], length=int(length),
                    expression=equation)
        clues.append(clue)
    for clue in clues:
        for evaluator in clue.evaluators:
            evaluator.globals()['div'] = my_div
            evaluator.globals()['pow'] = my_pow
    if use_10d:
        clues.append(Clue(f'10d', False, base_location=grid[10 - 1], length=3))
    return clues


def get_values():
    build_tables()
    clues = parse_clues()

    unseen_clues = set(clues)
    special = {clues[0], clues[1], clues[2]}
    seen_vars = set()
    results: list[dict[Any, Any]] = [{}]
    tables = {3: TABLES3, 4: TABLES4, 5: TABLES5}
    while unseen_clues:
        universe = unseen_clues & special
        universe = universe or unseen_clues
        clue = min(universe,
                   key=lambda clue: len(set(clue.evaluators[0].vars) - seen_vars))
        evaluator = clue.evaluators[0]
        new_vars = sorted(set(evaluator.vars) - seen_vars)
        if clue in special:
            expected_value = {'3d': 3, '4d': 6, '5d': 9}[clue.name]
            prev_seen_clue = next_seen_clue = None
        else:
            index = clues.index(clue)
            expected_value = None
            prev_seen_clue = next((clue for clue in reversed(clues[:index])
                                  if clue not in unseen_clues), None)
            next_seen_clue = next((clue for clue in clues[index + 1:]
                                   if clue not in unseen_clues), None)

        max_var_value = 3 if clue.name == '3d' else 10
        dict_updates = [dict(zip(new_vars, new_values))
                        for new_values in itertools.product(range(1, max_var_value + 1),
                                                            repeat=len(new_vars))]
        next_result = []
        if clue in special:
            for result in results:
                for dict_update in dict_updates:
                    temp = result | dict_update
                    value = -1 if not (x := evaluator(temp)) else int(x[0])
                    if value == expected_value:
                        temp[clue.name] = value
                        next_result.append(temp)
        else:
            table = tables[clue.length]
            for result in results:
                min_value = 9 if prev_seen_clue is None else result[prev_seen_clue.name]
                max_value = 100 if next_seen_clue is None else result[next_seen_clue.name]
                for dict_update in dict_updates:
                    temp = result | dict_update
                    value = -1 if not (x := evaluator(temp)) else int(x[0])
                    if value in table and min_value < value < max_value:
                        temp[clue.name] = value
                        next_result.append(temp)

        unseen_clues.remove(clue)
        seen_vars |= set(new_vars)
        results = next_result
        print(clue, new_vars, len(results))
    return results


class Magpie231Solver(ConstraintSolver):
    @staticmethod
    def run(result):
        solver = Magpie231Solver(result)
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self, result):
        self.result = result | {'10d': result['12a']}
        build_tables()
        clues = self.get_clues()
        super().__init__(clues)
        self.add_all_constraints()

    def get_clues(self) -> list[Clue]:
        clues = parse_clues(use_10d=True)
        for clue in clues:
            clue.generator = self.generator
        return clues

    def add_all_constraints(self):
        clues = ('3d', '4d', '5d', '13d', '15a', '1a', '12d', '8d', '11d', '2d', '6a',
                 '7a', '12a', '14a', '9a')
        for i, j in itertools.combinations(clues, 2):
            self.add_constraint((i, j), lambda x, y: int(x) < int(y))

    def generator(self, clue: Clue):
        length = clue.length
        table = TABLES3 if length == 3 else TABLES4 if length == 4 else TABLES5
        value = self.result[clue.name]
        if value < 10:
            result = {3: [111], 6: [112, 121, 211], 9: [122, 212, 122]}[value]
        else:
            result = table[value]
        return result

    def draw_grid(self, *, location_to_entry, **args: Any) -> None:
        return
        mapper = defaultdict(list)
        for letter in "abcdeghijklmnopqrstuvwxy".upper():
            mapper[self.result[letter]].append(letter.upper())
        mapper[1] = '*',
        location_to_entry = {location: ''.join(mapper[int(digit)])
                             for location, digit in location_to_entry.items()}
        super().draw_grid(location_to_entry=location_to_entry, **args)


def go():
    start = datetime.now()
    results = get_values()
    end = datetime.now()
    print(end - start)
    # for result in results:
    #     Magpie231Solver.run(result)


if __name__ == '__main__':
    go()
