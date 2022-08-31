import itertools
import math
import re
from collections import Counter, defaultdict
from fractions import Fraction
from typing import Callable, Pattern, Sequence, Union

from solver.fill_in_crossword_grid import FillInCrosswordGrid
from solver import Clue, ClueValue, EquationSolver, Intersection
from solver.equation_solver import KnownClueDict, KnownLetterDict

A_NUMBERS = """
H+ A − W 
E− R
I+ S
P− O
Y +E 
SU + E 
HE
A− N
S + I + C
UR
RY + E
AS
RI
G+ I
G+ O 
T+ O
U + T+ E
RO + Y 
H+A+L 
YE
RI+SK 
F+O +B 
R+YE
"""

A_CLUES = """
S(O**Y)
(Z + E)**N
MIM/E
(Q + U)/(A − R − K)
D(I + Z + Z)Y
(NO + T)**R + E − D + A + M − E
R**(O + Y) + (LY)**(L − E) 
X**(E + B − E − C)
F**Y − L**(F + O − T)
HI!
HO/(OF)
EOK/A
G/(E + N)
VOIV(O + D + E + S + H + I − P)
(G + R − E + N)ADA
H**(A − S) + T(E + N) + I + N + G 
H**A − R**(E + S)
SUN(N**Y)
KEX
M(U**R)/(D − O + C − H) 
((RA + T)/(H + E))**R
(E − N)(V**Y) 
T**(H + E − N)
"""

D_NUMBERS = """
H+ U −E 
D− O 
T− O− E 
S+ I− N 
C+ O− B
A− M 
US
O− R
C + O − L 
SO
A+ R − K 
O+ N
HI
HO
ER
A+ S 
HUH
M + O 
A+ N 
(SH)**Y
OR
P +O
YU
HU + T
"""

D_CLUES = """
(W**Y)/E
A + H + (O**Y)
S/(AY)
F + O/(U**R)
A/(R**Y)
(HOR − R)(O**R)
(H**I)/(GH + N(E + S + S))
DIRTYR(O + T + T + ER)
(H − I + TC)**H
(F + O + R + E)NOON
MUD
HUM/P
P/((E + A − L − E)D)
(XX − H)/(Y**Y − H) 
N**(O − R)
(J**(E − R − S))(E − Y) 
K**(E − E + N)
SIX/(P(E − N + C − E))
 PYX
P(LU − S)N(A + S + T + Y) 
LISLE
HUMM(O − C)K + IER
I(D + I − O + T − I + C + A + L + L)/Y 
DOR/Y
"""

GRID = """
X.XXX.X.XXX.X
X......XX....
.X...X.X.....
X..........X.
.X...X.......
X......XX....
X.X.XX...X..X
X.....XX..X..
X...X....X...
...X.X.......
X.......X....
X.....X......
X......X.....
"""


class Listener4725(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Listener4725()
        solver.solve(debug=False)

    def __init__(self):
        self.clue_count = 0
        self.a_numbers = self.get_clues(A_NUMBERS, False)
        self.a_clues = self.get_clues(A_CLUES, True)
        self.d_numbers = self.get_clues(D_NUMBERS, False)
        self.d_clues = self.get_clues(D_CLUES, True)

        assert len(self.a_numbers) == len(self.a_clues)
        assert len(self.d_numbers) == len(self.d_clues)

        clues = self.a_clues + self.a_numbers + self.d_clues + self.d_numbers

        super().__init__(clues, items=range(1, 27), allow_duplicates=True)

        def appropriate_count(*downs):
            counter = Counter(len(d) for d in downs)
            return all(x % 2 == 0 for x in counter.values())

        total_clues = len(self.a_numbers) + len(self.d_numbers)
        for c in (self.a_numbers, self.d_numbers):
            for index, a in enumerate(c):
                self.add_constraint((a,),
                                    lambda x, ix=index: ix <= int(x) <= total_clues)
            for a, b in itertools.combinations(c, 2):
                self.add_constraint((a, b), lambda x, y: int(x) < int(y))

        self.add_constraint((self.a_numbers[0], self.d_numbers[0]),
                            lambda x, y: int(x) == 1 or int(y) == 1)

        across_count = len(self.a_clues)
        for a, b in zip(self.a_clues[:across_count // 2], self.a_clues[::-1]):
            self.add_constraint((a, b), lambda x, y: len(x) == len(y))
        # There are an odd number of across clues.  So the middle one's length must be
        # odd like the width of the grid.
        self.add_constraint((self.a_clues[across_count // 2],), lambda x: len(x) & 1 == 1)

        self.add_constraint(self.d_clues, appropriate_count)

    def get_clues(self, lines, is_special):

        result: list[Clue] = []
        for line in lines.splitlines():
            line = line.strip()
            if not line:
                continue
            self.clue_count += 1
            clue = Clue(f'{self.clue_count}a', True, (1, 1), 1)
            if is_special:
                evaluator = Clue.create_evaluators(line, dict(fact=self.factorial))[0]
                evaluator = evaluator.with_alt_wrapper(self.my_wrapper)
                clue.evaluators = evaluator,
            else:
                clue.evaluators = Clue.create_evaluators(line)
            result.append(clue)
        return result

    @classmethod
    def my_wrapper(cls, evaluator, value_dict):
        result = evaluator.callable(*(Fraction(value_dict[x]) for x in evaluator.vars))
        assert isinstance(result, Fraction)
        if result <= 0:
            return ()
        if result.denominator == 1:
            return str(int(result)),
        temp = cls.handle_good_denominator(result)
        if temp:
            return temp
        else:
            return f'{result.numerator}/{result.denominator}',

    @staticmethod
    def handle_good_denominator(result):
        denominator, count2, count5 = result.denominator, 0, 0
        while denominator % 2 == 0:
            denominator, count2 = denominator // 2, count2 + 1
        while denominator % 5 == 0:
            denominator, count5 = denominator // 5, count5 + 1
        if denominator != 1:
            return ()
        count = max(count2, count5)
        result = str(int(result * 10 ** count)).rjust(count, '0')
        if len(result) == count:
            return ('0.' + result),
        else:
            return (result[:-count] + '.' + result[-count:]),

    PATTERN1 = re.compile(r"\d\d?")
    PATTERN2 = re.compile(r".{4,8}")

    def make_pattern_generator(self, clue: Clue, _: Sequence[Intersection]) -> \
            Callable[[dict[Clue, ClueValue]], Pattern[str]]:
        if clue in self.a_numbers or clue in self.d_numbers:
            return lambda _: self.PATTERN1
        else:
            return lambda _: self.PATTERN2

    def check_solution(self, known_clues: KnownClueDict, _: KnownLetterDict) -> bool:
        # Arrange clues by their clue number
        checker = defaultdict(list)
        for numbers, values in ((self.a_numbers, self.a_clues),
                                (self.d_numbers, self.d_clues)):
            for number_clue, value_clue in zip(numbers, values):
                clue_number = int(known_clues[number_clue])
                clue_value = known_clues[value_clue]
                checker[clue_number].append(clue_value)
        # If an across and down both have the same clue_number, they must have the same
        # first digit
        doubled_clues = [values for values in checker.values() if len(values) > 1]
        if any(values1[0] != values2[0] for values1, values2 in doubled_clues):
            return False
        # The clue numbers must run for 1 .. max(checker.keys())
        if any(i not in checker for i in range(1, max(checker.keys()))):
            return False
        return True

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict
                      ) -> None:
        def get_clues(numbers, values):
            return [(int(known_clues[clue1]), known_clues[clue2])
                    for clue1, clue2 in zip(numbers, values)]
        acrosses = get_clues(self.a_numbers, self.a_clues)
        downs = get_clues(self.d_numbers, self.d_clues)
        filler = FillInCrosswordGrid(acrosses, downs, size=13)
        results = filler.run()
        if results:
            self.show_letter_values(known_letters)
            for result in results:
                filler.display(result)

    @staticmethod
    def factorial(x: Union[int, Fraction]):
        if x >= 0 and x.denominator == 1:
            return math.factorial(x.numerator)
        else:
            raise ArithmeticError


if __name__ == '__main__':
    Listener4725.run()
