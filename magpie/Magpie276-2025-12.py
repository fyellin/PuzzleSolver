import functools
import io
import itertools
import multiprocessing
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from fractions import Fraction
from typing import Sequence

import math

from solver import Clue, ClueValue, Clues, ConstraintSolver, DancingLinks as DancingLinks, \
    Evaluator, Letter, MultiEquationSolver
from solver.equation_solver import KnownClueDict, KnownLetterDict

CLUES = """
a H! −E+A−D
b (R−E**I)D
c B+O+T+H+A−M
d ((H**(E−A)+D)/L)E+Y
e 0
f P+ I +E+T+ER+ S +E+N
g R+ (O+O)T
h (B−R+A)D+M−A−N
i H−A+L**E +S
j H**E(A+L)+Y
k G+(A+L)L(I −A)N
m (D+E)VI − (L+L)(I+E) − RS

n A+LI
p ((A+ S)/T)LE
q OL+D
r MI +L+LE+R
s I +L−O+TT
t (H+A+D)L+EE
u L+E−A+CH
v (L/I)LL−EE

w Q+A+DIR
x −P+A+T**E +L
y W(A+R+N−E)
z (S +T)O!−K−E−S
"""

ACROSS_LENGTHS = "321/132/213/312/231/123"
DOWN_LENGTHS = "222/1113/42/24/3111/222"

def my_pow(base, power):
    if math.log10(base) * abs(power) >= 10:
        raise ArithmeticError
    if power < 0:
        return Fraction(1, base ** -power)
    else:
        return base ** power

def my_div(numerator, denominator):
    return Fraction(numerator, denominator)

def my_fact(value):
    if value >= 8:
        raise ArithmeticError
    return math.factorial(value)

# Look at Magpie 256 when we're done

class Magpie276(MultiEquationSolver):
    MULTIPROCESSING = True

    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False, max_debug_depth=0, multiprocessing=True)
        # solver.solve(debug=True, max_debug_depth=1)

    def __init__(self) -> None:
        # clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 100), allow_duplicates=True, task_queue_size=2_000_000_000)
        self.initialize_constraints()

    def get_clues(self):
        clues = []
        mapping = dict(div=my_div, pow=my_pow, fact=my_fact)
        for line in CLUES.strip().splitlines():
            if not line:
                continue
            letter, expression = line[0], line[2:]
            if letter in 'abcdefnpqrstuv':
                length = 2
            elif letter in 'ghijkmwx':
                length = 3
            else:
                length = 4
            if is_across := (letter <= 'm'):
                position = len(clues) + 1, 1
            else:
                position = 1, len(clues) - 8
            clue = Clue(letter, is_across, position, length)
            if letter != 'e':
                clue.evaluators = Evaluator.create_evaluators(expression, mapping=mapping)
            else:
                clue.evaluators = Evaluator.create_evaluators(expression, wrapper=self.clue_e_wrapper)
                clue.priority = -1
            clues.append(clue)
        return clues

    def initialize_constraints(self):
        for clue1, clue2 in itertools.combinations(self._clue_list, 2):
            # Acrosses and downs each have to be strictly increasing
            if clue1.is_across == clue2.is_across and clue1.length == clue2.length:
                self.add_constraint((clue1, clue2), lambda x, y: x < y)
            # If two acrosses start with the same digit, it better be a "1" or a "2".
            # And if it's a "2", one of them has to be the extras "20".
            if clue1.is_across and clue2.is_across:
                self.add_constraint((clue1, clue2),
                                    lambda x, y: x[0] != y[0] or x[0] == '1' or x == '20' or y == '20')
            # If two downs end in the same digit, either one of them is the extras,
            # or else they are both '1' and at least one of them refers to 11
            if not clue1.is_across and not clue2.is_across:
                self.add_constraint((clue1, clue2),
                                    lambda x, y: x[-1] != y[-1] or int(x) <= 20 or int(y) <= 20 or \
                                                 (x.endswith('11') or y.endswith('11')))
                if clue1.length >= 3 and clue2.length >= 3:
                    self.add_constraint((clue1, clue2),
                                        lambda x, y: not (x.endswith('10') and y.endswith('10')))

        self.add_constraint(("a",), lambda x: x <= '20')  # the first number must be the extra or less.
        self.add_constraint(("b",), lambda x: x <= '59')
        self.add_constraint(("c",), lambda x: x <= '69')
        self.add_constraint(("d",), lambda x: x <= '79')
        self.add_constraint(("f",), lambda x: x >= '90')
        self.add_constraint(("g",), lambda x: "100" <= x <= "109")  # must be score for 10
        self.add_constraint(("h",), lambda x: x == "110") # We know that #11a scored a 0.
        self.add_constraint(("n",), lambda x: x <= '20')  # the first number must be the extra or less.

        for clue in self._clue_list:
            if clue.is_across:
                if clue.length == 3:
                    # If the second digit is a 0, it must be player #10a and not the first
                    # digit of a score.
                    self.add_constraint([clue], lambda x: x[0] == '1' or x[1] != '0')
                if clue.name != 'e':
                    self.add_constraint([clue], lambda x: x[0] != '8')
            else:
                if clue.length == 2:
                    # Two digit answers that end in 0 have to be "extra" which is 10 or 20
                    self.add_constraint([clue], lambda x: x <= '20' or x[1] != '0')
                else:
                    # 3/4 digit answers that end in 0 must be player #10
                    self.add_constraint([clue], lambda x: x[-1] != '0' or x[-2] == '1')

        # One of y or z has to be the century scored by 1 or 2
        # The other has to be a two-digit number followed by 10 or 11
        def is_century(value):
            return '1' <= value[3] <= '2' and '100' <= value[0:3] <= '199'

        def is_ten_eleven(value):
            return '10' <= value[2:4] <= '11'
        self.add_constraint(("y",), lambda x: is_century(x) or is_ten_eleven(x))
        self.add_constraint(("z",), lambda x: is_century(x) or is_ten_eleven(x))
        self.add_constraint(("y", "z"),
                            lambda x, y: (is_century(x) and is_ten_eleven(y)) or (is_century(y) and is_ten_eleven(x)))

        # If "n" has to be the extra (because "p" is too big) then n == "a" or n >= "b"
        self.add_constraint(("a", "b", "n", "p"),
                            lambda a, b, n, p:  p <= '20' or n == a or n >= b)
        # Same thing the other way around.
        self.add_constraint(("a", "b", "n", "p"),
                            lambda a, b, n, p:  b <= '20' or a == n or a >= p)

        # Players #10d and #11d have to be three or four digits, and there are only four
        # such clues.
        def ten_eleven_down(w, x, y, z):
            temp = (w[1:], x[1:],  y[2:], z[2:])
            return "10" in temp and "11" in temp
        self.add_constraint(("w", "x", "y", "z"), ten_eleven_down)

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        count = len(letters)
        if count == 0:
            yield ()
            return

        match (count, letters[0]):
            case 1, 'E': yield from ((x,) for x in range(1, 10)) # 10**2 is too big
            case 1, 'H': yield from ((x,) for x in range(1, 6))  # 6! is too big
            case _: yield from super().get_letter_values(known_letters, letters)
        return

    def clue_e_wrapper(self, _wrapper, letters: dict[Letter, int]) -> Iterable[ClueValue]:
        if not any(isinstance(x, Clue) for x in letters.values()):
            temp = {clue: str(clue.evaluators[0].raw_call(letters))
                    for clue in self._clue_list if clue.name != 'e'}
            letters = temp | letters

        acrosses, downs = set(), set()
        for key, value in letters.items():
            if isinstance(key, Clue):
                (acrosses if key.name <= 'm' else downs).add(value)
        assert len(acrosses) == 11
        assert len(downs) == 12
        extras = acrosses.intersection(downs)
        if len(extras) != 1:
            return ()
        extras = extras.pop()
        acrosses.remove(extras)
        downs.remove(extras)

        a10 = [x for x in acrosses if '100' <= x <= '109']
        assert len(a10) == 1
        a10, = a10
        assert '110' in acrosses
        a11 = '110'
        acrosses -= {a10, a11}  # acrosses now has length 8
        across_players = {x[0] for x in acrosses}
        if len(across_players) != 8 or '8' in across_players:
            return ()
        scores = [int(a10[2:]), int(a11[2:]), 8, *(int(x[1:]) for x in acrosses)]
        if scores.count(0) != 2:
            return ()
        across_total = sum(scores) + int(extras)
        if not 203 <= across_total <= 207:
            return ()

        down_totals = set()
        d10s = [x for x in downs if len(x) >= 3 and x.endswith('10')]
        d11s = [x for x in downs if len(x) >= 3 and x.endswith('11')]
        for d10, d11 in itertools.product(d10s, d11s):
            other_values = downs - {d10, d11}
            down_players = {x[-1] for x in other_values}
            if len(down_players) != 9 or '0' in down_players:
                continue
            down_total = int(d10) // 100 + int(d11) // 100
            down_total += sum(int(x) // 10 for x in other_values) + int(extras)
            if 204 <= down_total <= 207:
                down_totals.add(down_total)
        if not down_totals:
            return ()

        return tuple(ClueValue(str(88 + delta)) for delta in (0, 1) if across_total + delta in down_totals)

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        result = [known_clues[clue] for clue in self._clue_list]
        dl = MyDancingLinks()
        results = dl.dancing_links(known_clues)
        for result in results:
            solution = {dl.clue_named(key): value for key, value in result}
            dl.show_solution(solution)

"""
g  ORT  R+ (O+O)T
s  IL   I +L−O+TT
v  E    v (L/I)LL−EE
b  E    (R−E**I)D
q  ()   OL+D
n  A    A+LI
x  P    −P+A+T**E +L
w  Q    Q+A+DIR
a  H    H! −E+A−D
t  -    (H+A+D)L+EE
i  S    H−A+L**E +S
p  -    ((A+ S)/T)LE
z  K    (S +T)O!−K−E−S
j  Y    H**E(A+L)+Y
d  -    ((H**(E−A)+D)/L)E+Y
m  V    (D+E)VI − (L+L)(I+E) − RS
f  N    P+ I +E+T+ER+ S +E+N
y  W    W(A+R+N−E)
k  G    G+(A+L)L(I −A)N
r  M    MI +L+LE+R
h  B    (B−R+A)D+M−A−N
c  -    B+O+T+H+A−M
u  C    L+E−A+CH

"""

class FastConstraintSolver:
    def __init__(self, *, prefix = None):
        self.solver = Magpie276()
        self.solver._debug = False
        self.solving_order = self.solver._get_solving_order()
        self.prefix = prefix or "/tmp"

    def file_name_for_index(self, index) -> str:
        clue, *_ = self.solving_order[index]
        return f"{self.prefix}/solve_{index:02}_{clue.name}.txt"

    @functools.cache
    def get_coders_for_index(self, index):
        clues = []
        variables = []
        for i in range(0, index + 1):
            clue, evaluator, clue_letters, _, constraints = self.solving_order[i]
            clues.append(clue)
            variables.extend(clue_letters)
        clues: list[Clue] = sorted(clues, key=lambda x: x.name)
        variables: list[Letter] = sorted(variables)
        letters_slice = slice(len(clues), None)

        def decode_line(line:str) -> tuple[KnownClueDict, KnownLetterDict]:
            values = line.split()
            known_clues = dict(zip(clues, values))
            known_letters = dict(zip(variables, (int(x) for x in values[letters_slice])))
            return known_clues, known_letters

        def encode_line(known_clues: KnownClueDict, known_letters: KnownLetterDict) -> str:
            info = [*[known_clues[clue] for clue in clues], *[str(known_letters[v]) for v in variables]]
            return ' '.join(info)

        return decode_line, encode_line

    def run_all_passes(self, start=0):
        for item in self.solving_order:
            print(item.clue, ''.join(item.letters) or '-', item.evaluator)

        for i in range(start, len(self.solving_order)):
            self.run_one_pass(i)

    def run_one_pass(self, index):
        if index == 0:
            file = io.StringIO("\n")
        else:
            file = open(self.file_name_for_index(index - 1))

        in_count = out_count = 0
        clue, evaluator, clue_letters, _, constraints = self.solving_order[index]
        print(f'{index} {clue.name} {"".join(clue_letters)}', end='')
        with file, open(self.file_name_for_index(index), "w") as output:
            with multiprocessing.Pool(initializer=self.pool_initializer) as pool:
                if self.solver.MULTIPROCESSING:
                    results = pool.imap_unordered(self.bridge,
                                                  ((lines, index) for lines in itertools.batched(file, 100)),
                                                  chunksize=100)
                else:
                    results = (self.inner_pass(lines, index) for lines in itertools.batched(file, 100))
                for result in results:
                    in_count += 100  # same as itertools.batched, above
                    if (in_count % 1_000_000) == 0:
                        print('.', end='')
                    for r in result:
                        out_count += 1
                        if (out_count % 1_000_000) == 0:
                            print('+', end='')
                        print(r, file=output)
        print(f' {in_count:,} -> {out_count:,}')

    def inner_pass(self, lines, index):
        solver = self.solver
        clue, evaluator, clue_letters, _, constraints = self.solving_order[index]
        old_decoder, _ = self.get_coders_for_index(index - 1)
        _, new_encoder = self.get_coders_for_index(index)
        results = []

        for line in lines:
            known_clues, known_letters = old_decoder(line)
            for next_letter_values in solver.get_letter_values(known_letters, clue_letters):
                known_letters.update(zip(clue_letters, next_letter_values))
                clue_values = evaluator(known_letters)
                if not clue_values:
                    continue
                clue_value, = clue_values

                if len(clue_value) != clue.length:
                    continue

                known_clues[clue] = clue_value
                if constraints:
                    solver._known_clues = known_clues
                    if not all(constraint() for constraint in constraints):
                        continue
                results.append(new_encoder(known_clues, known_letters))
        solver._known_clues = None
        return results

    @staticmethod
    def pool_initializer():
        global FOOBAR
        FOOBAR = FastConstraintSolver()

    @staticmethod
    def bridge(arglist):
        global FOOBAR
        lines, index = arglist
        return FOOBAR.inner_pass(lines, index)

    def see_common_values(self, index):
        decoder, encoder = self.get_coders_for_index(index)

        result = defaultdict(set)

        with open(self.file_name_for_index(index)) as file:
            for line in file:
                dictionary = decoder(line)
                for key, value in dictionary.items():
                    result[key].add(value)

        for key, value in result.items():
            if len(value) <= 10 or True:
                print(key, value)

class MyDancingLinks (ConstraintSolver):
    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues)

    @classmethod
    def test_run(cls):
        other_solver = Magpie276()
        for result in FOOBAR:
            known_clues = dict(zip(other_solver._clue_list, result))
            solver = cls()
            results = solver.dancing_links(known_clues)
            for result in results:
                solution = {solver.clue_named(key): value for key, value in result}
                solver.show_solution(solution)

    def dancing_links(self, solution, debug=0, show=False):
        across_clues = [value for key, value in solution.items() if key.name <= 'm']
        down_clues = [value for key, value in solution.items() if key.name >= 'n']

        optional_constraints = {f'r{r}c{c}' for r in range(1, 7) for c in range(1, 7)}
        constraints = {}
        for clue in self._clue_list:
            code = 'aa' if clue.is_across else 'dd'
            for value in (across_clues if clue.is_across else down_clues):
                if len(value) != clue.length:
                    continue
                constraint = [f'{clue.name}', f'{value}{code}']
                constraint.extend((f'r{r}c{c}', letter)
                                  for (r, c), letter in zip(clue.locations, value))
                constraints[(clue.name, value)] = constraint
        intersection, = [x for x in across_clues if x in down_clues]

        across_twos = [clue for clue in self._clue_list if clue.length == 2 and clue.is_across]
        down_twos = [clue for clue in self._clue_list if clue.length == 2 and not clue.is_across]
        for clue1, clue2 in itertools.product(across_twos, down_twos):
            if not any(clue1.locations[i] == clue2.locations[i] for i in range(2)):
                constraint = f'{clue1.name}≠{clue2.name}'
                constraints[(clue1.name, intersection)].append(constraint)
                constraints[(clue2.name, intersection)].append(constraint)
                optional_constraints.add(constraint)

        results = []
        solver = DancingLinks(constraints, optional_constraints=optional_constraints, row_printer=lambda x: results.append(x))
        solver.solve(debug=debug)
        if show:
            for result in results:
                solution = {self.clue_named(key): value for key, value in result}
                self.show_solution(solution)

        return results

FOOBAR = [
['14', '16', '30', '53', '89', '97', '101', '110', '226', '489', '631', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '51', '89', '97', '101', '110', '226', '487', '611', '743', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '52', '89', '97', '101', '110', '226', '488', '631', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '53', '88', '97', '101', '110', '226', '489', '630', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '54', '88', '97', '101', '110', '226', '490', '628', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '55', '89', '97', '101', '110', '226', '491', '625', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '55', '88', '97', '101', '110', '226', '491', '626', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '57', '89', '97', '101', '110', '226', '493', '621', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '57', '88', '97', '101', '110', '226', '493', '622', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '58', '89', '97', '101', '110', '226', '494', '619', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '58', '88', '97', '101', '110', '226', '494', '620', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '59', '89', '97', '101', '110', '226', '495', '617', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '59', '88', '97', '101', '110', '226', '495', '618', '721', '13', '16', '38', '61', '84', '87', '96', '99', '195', '710', '1012', '1811'],
['14', '16', '30', '53', '89', '97', '101', '110', '226', '489', '630', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '53', '88', '97', '101', '110', '226', '489', '631', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '54', '89', '97', '101', '110', '226', '490', '628', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '54', '88', '97', '101', '110', '226', '490', '629', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '57', '89', '97', '101', '110', '226', '493', '622', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '57', '88', '97', '101', '110', '226', '493', '623', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '59', '89', '97', '101', '110', '226', '495', '618', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '59', '88', '97', '101', '110', '226', '495', '619', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '51', '88', '97', '101', '110', '226', '487', '613', '743', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '52', '88', '97', '101', '110', '226', '488', '633', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '55', '89', '97', '101', '110', '226', '491', '626', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '58', '89', '97', '101', '110', '226', '494', '620', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '58', '88', '97', '101', '110', '226', '494', '621', '721', '13', '16', '38', '61', '84', '87', '96', '99', '205', '710', '1012', '1811'],
['14', '16', '30', '51', '89', '97', '101', '110', '226', '487', '613', '743', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '52', '89', '97', '101', '110', '226', '488', '633', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '52', '88', '97', '101', '110', '226', '488', '634', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '54', '89', '97', '101', '110', '226', '490', '629', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '55', '88', '97', '101', '110', '226', '491', '628', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '58', '89', '97', '101', '110', '226', '494', '621', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '58', '88', '97', '101', '110', '226', '494', '622', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '59', '89', '97', '101', '110', '226', '495', '619', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '59', '88', '97', '101', '110', '226', '495', '620', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '57', '89', '97', '101', '110', '226', '493', '623', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
['14', '16', '30', '57', '88', '97', '101', '110', '226', '493', '624', '721', '13', '16', '38', '61', '84', '87', '96', '99', '215', '710', '1012', '1811'],
]


if __name__ == '__main__':
    start = datetime.now()
    match 0:
        case 0:
            MyDancingLinks.test_run()

        case 1:
            Magpie276.run()
    end = datetime.now()
    print(end - start)

