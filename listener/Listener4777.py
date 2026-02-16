import math
import re
from itertools import combinations, count, pairwise

from misc.factors import factor_list, prime_factors
from solver import Clue, ConstraintSolver, EquationSolver, Evaluator, Location, generators
from solver import KnownClueDict, KnownLetterDict

GRID = [
    (112, 132, 153, 213, 242, 262, 312, 332, 353, 417, 513, 542, 562, 612, 632, 653, 713,
     742, 762),
    (113, 122, 133, 147, 163, 322, 352, 372, 412, 432, 462, 523, 553, 573, 662)
]

ACROSSES = """
1 B + Y (2)
2 IN (2)
3 C + K (2)
4 DF (2)
5 C' (2)
6 C + FT (2)
7 L' (2)
8 B**N − N (2)
9 NR**N (2)
10 A! − (IR)' (2)
11 GNT (2)
12 IJ (3)
13 (AEI)' (3)
14 I'(N**A)' (3)
15 ((C + K)N**A)' (3)
16 AE**A (2)
17 (G! + I'K)' (3)
18 D + E**FJR (3)
"""

DOWNS = """
20 T (2)
21 I (2)
22 BR (2)
23 (B + D)(J − D)N (2)
24 C + I + J + K + L + T (2)
25 F(C + K) (2)
26 (JL')' (3)
27 A(AJ − O) (3)
28 (CER)' (2)
29 F**A − DT (2)
30 D(D**N − G) (3)
31 AL'NT (3)
32 (LY − O)RY (3)
33 K'(ND**N − M!) (3)
"""


class Solver1(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=range(0, 17))
        for clue1, clue2 in combinations(clues, 2):
            if clue1.context == clue2.context:
                self.add_constraint((clue1, clue2), lambda x, y: int(x) < int(y))

    def get_clues(self):
        mapping = {'fact': self.my_fact, 'prime':  self.my_prime}
        result: list[Clue] = []
        for lines, is_across in ((ACROSSES, True), (DOWNS, False)):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                location = (1 + len(result), 1)
                expression = match.group(2).strip()
                clue = Clue(f'{number}', True, location, int(match.group(3)),
                            context=is_across)
                clue.expression = expression
                clue.evaluators = Evaluator.create_evaluators(expression, mapping=mapping)
                result.append(clue)
        return result

    def show_solution(self, known_clues: KnownClueDict,
                      known_letters: KnownLetterDict) -> None:
        self.show_letter_values(known_letters)
        acrosses, downs = [], []
        for clue in self._clue_list:
            result = (int(known_clues[clue]), clue.length)
            (acrosses if clue.context else downs).append(result)
        temp = {value: letter for letter, value in known_letters.items()}
        letters = ''.join(temp[i] for i in range(0, 17))
        Solver2.run(acrosses, downs, letters)

    @staticmethod
    def my_fact(x):
        if x < 0 or x == 1:
            raise ArithmeticError
        return math.factorial(x)

    @staticmethod
    def my_prime(x):
        if x < 10 or x % 10 == 0:
            raise ArithmeticError
        result = int(str(x)[::-1])
        if result == x:
            raise ArithmeticError
        return result

    def get_allowed_regexp(self, location: Location) -> str:
        return r"(\d|1[0-6])"


class Solver2(ConstraintSolver):
    @classmethod
    def run(cls, across=None, down=None, letters=None):
        across = across or (
            ('17', 2), ('26', 2), ('29', 2), ('40', 2), ('51', 2), ('59', 2), ('61', 2),
            ('79', 2), ('98', 2), ('101', 2), ('132', 2), ('156', 3), ('591', 3),
            ('713', 3), ('829', 3), ('1215', 2), ('4511', 3), ('6814', 3))
        down = down or (
            ('11', 2), ('13', 2), ('63', 2), ('76', 2), ('81', 2), ('116', 2), ('237', 3),
            ('300', 3), ('513', 2), ('914', 2), ('940', 3), ('6710', 3), ('7168', 3),
            ('8159', 3))
        letters = letters or "OMNEFAGRYBDTJIKCL"

        try:
            solver = cls(across, down, letters)
        except ArithmeticError:
            return
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self, across, down, letters):
        self.letters = letters
        self.encoding_to_plain = {}
        clues = self.get_clues(across, down)
        super().__init__(clues)
        for clue1, clue2 in combinations(clues, 2):
            if clue1.length == clue2.length:
                self.add_constraint((clue1, clue2),
                                    lambda x, y: self.encoding_to_plain[x] != self.encoding_to_plain[y])

    def get_clues(self, across, down):
        across_values = self.parse_clues(across)
        down_values = self.parse_clues(down)
        clues = []
        for is_across, values, starts in zip(
                (True, False), (across_values, down_values), GRID):
            generator = generators.known(*values)
            for start in starts:
                row, column, length = [int(x) for x in str(start)]
                name = f'{row}{column}{"A" if is_across else "D"}'
                clue = Clue(name, is_across, (row, column), length,
                            generator=(generator if length < 7 else None))
                clues.append(clue)
        return clues

    def parse_clues(self, value_list):
        # This could need to be more complicated, but we haven't found a case where
        # the reduction is ambiguous.
        result = []
        for value, length in value_list:
            value = str(value)
            if len(value) == length:
                result.append(value)
                self.encoding_to_plain[value] = value
            else:
                values = { value }
                for _ in range(len(value) - length):
                    values = {x for v in values for x in self.shorten(v) }
                if not values:
                    raise ArithmeticError(f'Cannot reduce {value} to length {length}')
                result.extend(values)
                self.encoding_to_plain |= {v : value for v in values}
        return result

    def shorten(self, value):
        for i, (a, b) in enumerate(pairwise(value)):
            if a == '1' and '0' <= b <= '6':
                yield value[0:i] + chr(ord(b) - ord('0') + ord('a')) + value[i+2:]

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        location_to_digit = {location : digit for clue, value in known_clues.items()
                             for location, digit in zip(clue.locations, value)}
        location_to_digit[4,4] = 'X'
        special_clues = [self.clue_named('14D'), self.clue_named('41A')]
        special_values = [''.join(location_to_digit[location] for location in clue.locations)
                          for clue in special_clues]
        self.result_digits = []
        for digit in '0123456789abcdefg':
            real_values = [value.replace('X', digit).replace('a', '10').replace('b', '11').replace('c', '12') \
                                .replace('d', '13').replace('e', '14').replace('f', '15').replace('g', '16')
                           for value in special_values]
            if all(self.is_prime_square(int(x[::-1])) for x in real_values):
                self.result_digits.append(digit)
        return bool(self.result_digits)

    def draw_grid(self, location_to_entry, location_to_clue_numbers, **more_args):
        my_dict = dict(zip("0123456789abcdefg", self.letters))
        location_to_clue_numbers.clear()
        for digit in self.result_digits:
            location_to_entry[4,4] = digit

            for location, value in location_to_entry.items():
                location_to_entry[location] = my_dict[value]
            super().draw_grid(location_to_entry=location_to_entry,
                              location_to_clue_numbers=location_to_clue_numbers,
                              subtext="JIMMY",
                              **more_args)
            super().draw_grid(location_to_entry=location_to_entry,
                              location_to_clue_numbers=location_to_clue_numbers,
                              subtext="ROGER",
                              **more_args)


    @staticmethod
    def is_prime_square(x):
        factors = prime_factors(x)
        evens = [count for _prime, count in factors if count % 2 == 0]
        odds = [count for _prime, count in factors if count % 2 == 1]
        if len(evens) == 0:
            result = odds == [3]
        else:
            result = odds == [1]
        return result


RUN = 1

if __name__ == '__main__':
    if RUN == 1:
        Solver1.run()
    else:
        Solver2.run()
