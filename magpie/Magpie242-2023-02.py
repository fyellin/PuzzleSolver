import itertools
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

from solver import Clue, Clues, ConstraintSolver, generators, KnownClueDict
from solver.generators import allvalues, known


@dataclass
class Permutation:
    permutation: tuple[int]
    translation: Any
    untranslation: Any
    name: str

    @staticmethod
    def from_perm(permutation):
        result = ''.join(str(x) for x in permutation)
        translation = str.maketrans("0123456789", result)
        untranslation = str.maketrans(result, "0123456789")
        return Permutation(permutation, translation, untranslation, result)

    def encode(self, value: str | int) -> str:
        value = str(value)
        if self.is_even_sum(value):
            return value
        return value.translate(self.translation)

    def _encode(self, value: str | int) -> str:
        return value.translate(self.translation)

    def unencode(self, value: str | int) -> str:
        value = str(value)
        if self.is_even_sum(value):
            return value
        return value.translate(self.untranslation)

    @staticmethod
    def get_all_permutations():
        temp = [p for p in itertools.permutations(range(5))
                if all(a != b for a, b in enumerate(p))]
        temp1 = [tuple(y * 2 for y in p) for p in temp]
        temp2 = [tuple(y * 2 + 1 for y in p) for p in temp]
        result = [tuple(x for y in zip(even, odd) for x in y) for even in temp1 for odd in
                  temp2]
        return [Permutation.from_perm(x) for x in result]

    @staticmethod
    def is_even_sum(value):
        return sum(int(x) for x in str(value)) % 2 == 0

    def permute(self):
        unseen = set('0123456789')
        result = ''
        while unseen:
            cycle = [min(unseen)]
            while True:
                next = self._encode(cycle[-1])
                if next == cycle[0]:
                    break
                cycle.append(next)
            unseen -= set(cycle)
            result += '(' + ', '.join(cycle) + ')'
        return result

    def __repr__(self):
        return self.name


CODES = Permutation.get_all_permutations()
SQUARES = set(x * x for x in range(1, 1000))

PRIMES2 = [x for x in range(10, 100) if x % 2 and x % 3 and x % 5 and x % 7]
TRIANGLES3 = [y for x in range(1, 100) for y in [x * (x + 1) // 2] if 100 <= y <= 999]


# Variables like a1 refer to the answer to the clue, while aa1 refers to the entry in the
# grid.
def run():
    for code in CODES:
        for a16 in (str(x * x) for x in range(10, 32)):
            aa16 = code.encode(a16)
            if aa16.startswith('0'):
                continue
            seen = {a16, aa16}
            # Determine a3 and aa3.
            a3 = aa16[::-1]
            aa3 = code.encode(a3)
            if a3 in seen or aa3 in seen or '0' in aa3:  # No digit can be 0
                continue
            # We know aa3 must be a square and 14d is its square root.
            if int(aa3) not in SQUARES:
                continue
            seen |= {a3, aa3}
            d14 = str(math.isqrt(int(aa3)))
            dd14 = code.encode(d14)
            if dd14.startswith('0') or d14 in seen or dd14 in seen or dd14[1] != aa16[1]:
                continue
            seen = seen | {d14, dd14}
            # Look at possible values for d13, which is a multiple of dd14
            for d13 in [str(x) for x in range(2 * int(dd14), 100, int(dd14))]:
                dd13 = code.encode(d13)
                # Must match across clue.  Other digit can't be zero, either
                if '0' in dd13 or dd13[1] != aa16[0] or d13 in seen or dd13 in seen:
                    continue
                # Magpie242.run(code, a3=a3, a16=a16, d14=d14, d13=d13)
                run2(code, a3=a3, a16=a16, d14=d14, d13=d13)


def run2(code, **values):
    seen = {x for info in values.values() for x in (info, code.encode(info))}
    a3 = values['a3']
    aa3 = code.encode(a3)
    for d5 in (str(x) for x in PRIMES2):
        dd5 = code.encode(d5)
        if '0' in dd5 or dd5[0] != aa3[2] or d5 in seen or dd5 in seen:
            continue
        seen2 = seen | {d5, dd5}
        for a6 in (str(x) for x in range(10, int(dd5)) if int(dd5) % x == 0):
            aa6 = code.encode(a6)
            if '0' in aa6 or a6 in seen2 or aa6 in seen2:
                continue
            # run3(code, d5=d5, a6=a6)
            if values['d13'][0] not in '02468':
                continue
            # Magpie242(code).print(d5=d5, a6=a6, **values,
            #                       a1=41, d8=253, a15=10, d4=47, a12=576, a9=487)
            Magpie242.run(code, d5=d5, a6=a6, **values)


def run3(code, **values):
    seen = {x for info in values.values() for x in (info, code.encode(info))}
    for a1 in [str(x) for x in range(10, 100)]:
        aa1 = code.encode(a1)
        if a1 in seen or aa1 in seen or '0' in aa1 or int(a1) + int(aa1) not in SQUARES:
            continue
        run4(code, a1=a1, **values)


def run4(code, **values):
    seen = {x for info in values.values() for x in (info, code.encode(info))}
    for d8 in (str(x) for x in TRIANGLES3):
        dd8 = code.encode(d8)
        if '0' in dd8 or d8 in seen or dd8 in seen:
            continue
        seen2 = seen | {d8, dd8}
        a15 = str(sum(int(x) for x in dd8))
        aa15 = code.encode(a15)
        if len(aa15) < 2 or aa15[0] != dd8[2] or a15 in seen2 or aa15 in seen2:
            continue
        Magpie242.run(code, a15=a15, d8=d8, **values)


GRID = """
XXXXXXX
XX..XX.
X.XX...
X.X..X.
"""


class Magpie242(ConstraintSolver):
    @staticmethod
    def run(code, **values):
        print(code)
        print(values)
        solver = Magpie242(code, **values)
        solver.solve(debug=True)

    def print(self, **values):
        seen = {}
        for clue in self._clue_list:
            alt_name = clue.name[-1] + clue.name[:-1]
            if alt_name in values:
                seen[clue] = self.code.encode(values[alt_name])
        self.plot_board(seen)

    def __init__(self, code, **values):
        self.code = code
        clues = self.get_clue_list(code, **values)
        super().__init__(clues)
        self.get_constraints()

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        seen = set()
        for value in known_clues.values():
            if value in seen or self.code.unencode(value) in seen:
                return False
            seen |= {value, self.code.unencode(value)}
        aa17 = known_clues[self.clue_named('17a')]
        a17 = self.code.unencode(aa17)
        for clue, value in known_clues.items():  # note, encoded
            product = str(math.prod(int(x) for x in value))
            if product == a17:
                return True
        return False

    # a6 = a6, a15 = a15, d5 = d5, d8 = d8,
    def get_clue_list(self, code, a1=None, a3=None, a16=None, d13=None,
                      d14=None, a6=None, a15=None, d5=None, d8=None,  **_arg):
        def singleton(value):
            return known(code.encode(value))

        across = ((1, 2, singleton(a1) if a1 else allvalues),
                  (3, 3, singleton(a3) if a3 else allvalues),
                  (6, 2, singleton(a6) if a6 else allvalues),
                  (9, 3, self.encoded_prime),
                  (10, 3, allvalues),
                  (12, 3, allvalues),
                  (14, 3, allvalues),
                  (15, 2, singleton(a15) if a15 else allvalues),
                  (16, 3, singleton(a16) if a16 else self.encoded_square),
                  (17, 2, allvalues))
        downs = ((2, 3, allvalues),
                 (4, 2, self.encoded_prime),
                 (5, 2, singleton(d5) if d5 else self.encoded_prime),
                 (7, 3, allvalues),
                 (8, 3, singleton(d8) if d8 else self.encoded_triangle),
                 (11, 3, allvalues),
                 (13, 2, singleton(d13) if d13 else allvalues),
                 (14, 2, singleton(d14) if d14 else allvalues))
        locations = Clues.get_locations_from_grid(GRID)
        clues = [Clue(f'{location}{suffix}', is_across, locations[location - 1], length,
                      generator=generator)
                 for is_across, suffix, clue_set in (
                     (True, 'a', across), (False, 'd', downs))
                 for (location, length, generator) in clue_set]
        return clues

    def get_constraints(self):
        encode = self.code.encode
        unencode = self.code.unencode

        def is_multiple(a, b):
            temp = unencode(a)
            if temp[0] == '0':
                return False
            result = a != b and temp != b and int(temp) % int(b) == 0
            return result

        def is_factor(a, b):
            temp = unencode(a)
            if temp[0] == '0':
                return False
            result = a != b and temp != b and int(b) % int(temp) == 0
            return result

        def is_square_root(a, b):
            temp = unencode(a)
            if temp[0] == '0':
                return False
            return int(temp) ** 2 == int(b)

        def is_reverse(a, b):
            temp = unencode(a)
            if temp[0] == '0':
                return False
            return temp[::-1] == b

        def self_sum_square(a):
            temp = unencode(a)
            if temp[0] == '0':
                return False
            return int(temp) + int(a) in SQUARES

        def is_permutation(a, b):
            a, b = Counter(unencode(a)), Counter(b)
            return a == b

        def is_sum(x, a, b):
            return x == encode(int(a) + int(b))

        def is_digit_sum(x, a):
            return x == encode(sum(int(x) for x in a))

        def is_opposite_parity(a, b):
            return (int(a) + int(b)) & 1 == 1

        self.add_constraint(('1a',), self_sum_square)
        self.add_constraint(('3a', '16a'), is_reverse)
        self.add_constraint(('6a', '5d'), is_factor)
        self.add_constraint(('10a', '7d'), is_permutation)
        self.add_constraint(('12a', '9a', '2d'), is_sum)
        self.add_constraint(('14a', '14d'), is_multiple)
        self.add_constraint(('15a', '8d'), is_digit_sum)
        self.add_constraint(('17a', '12a'), is_factor)
        self.add_constraint(('2d', '13d'), is_opposite_parity)
        self.add_constraint(('11d', '14a', '7d'), is_sum)
        self.add_constraint(('13d', '14d'), is_multiple)
        self.add_constraint(('14d', '3a'), is_square_root)

    def encoded_prime(self, clue: Clue):
        for value in generators.prime(clue):
            yield self.code.encode(value)

    def encoded_triangle(self, clue: Clue):
        for value in generators.triangular(clue):
            yield self.code.encode(value)

    def encoded_square(self, clue: Clue):
        for value in generators.square(clue):
            yield self.code.encode(value)


if __name__ == '__main__':
    run()
    # run()
