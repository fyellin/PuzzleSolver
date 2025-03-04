import ast
import itertools
import math
from collections import defaultdict
from fractions import Fraction

from solver import Clue, Clues, ConstraintSolver, DancingLinks, Encoder, generators
from solver.constraint_solver import Constraint
from solver.equation_parser import EquationParser
from solver.equation_solver import KnownClueDict
from solver.generators import known, prime_generator


def hmean(*x):
    h = sum(Fraction(1, int(i)) for i in x) / len(x)
    if h.numerator == 1:
        return h.denominator

def amean(*x):
    m = sum(int(i) for i in x) / len(x)
    return m == int(m) and m

def gmean(*x):
    m = math.prod(int(i) for i in x)
    result = round(m ** (1 / len(x)))
    return result ** len(x) == m and result


def run_me1():
    count1 = count2 = 0
    for a, b, c, d in itertools.combinations(range(10, 100), 4):
        count1 += 1
        if (t := math.isqrt(math.isqrt(p := a * b * c * d))) ** 4 != p:
            continue
        h = sum(Fraction(1, x) for x in (a, b, c, d)) / 4
        if h.numerator == 1:
            print(f'(20a, 21a, 2d, 19d) {a}, {b}, {c}, {d}, 1d=ari={(a + b + c + d) / 4} 1a=geo={t}, 16d=har={h.denominator}')
            count2 += 1
    # 21, 28, 63, 84  geom=42,  harm=36
    print(count1, count2)

def run_me2():
    count1 = count2 = 0
    for a, b, c in itertools.combinations(range(10, 100), 3):
        for e in range(100, 400 - a - b - c):
            count1 += 1
            d, r = divmod(a + b + c + e, 4)
            if r != 0: continue
            if d >= 100: break
            p = a * b * c * d * e
            if (t := round(p ** 0.2)) ** 5 != p:
                continue
            h = sum(Fraction(1, x) for x in (a, b, c, d, e)) / 5
            if h.numerator == 1:
                print(f'(3a, 5a, 22a, 4d, (6d)) {a}, {b}, {c}, {d}, {e}, 6d=ari={d}, 9d=geo={t}, 12d=har={h.denominator}')
                count2 += 1
    print(count1, count2)


ACROSS = "222/42/33/33/24/222"
DOWN="222/24/33/33/42/222"


class Magpie264 (ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True)

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        super().__init__(clues,)
        self.setup()


    def setup(self):
        # (20a, 21a, 2d, 19d) 21, 28, 63, 84, 1d=arith=49.0 1a=geo=42, 16d=har=36
        self.clue_named("20a").generator = generators.known(63)
        self.clue_named("21a").generator = generators.known(84)
        self.clue_named("2d").generator = generators.known(21,)
        self.clue_named("19d").generator = generators.known(28)
        self.clue_named("1d").generator = generators.known(49)
        self.clue_named("1a").generator = generators.known(42)
        self.clue_named("16d").generator = generators.known(36)

        #(3a, 5a, 22a, 4d, (6d)) 18, 27, 81, 72, 162, 6d=ari=72, 9d=geo=54, 12d=har=40
        self.clue_named("3a").generator = generators.known(81)
        self.clue_named("5a").generator = generators.known(27)
        self.clue_named("22a").generator = generators.known(18)
        self.clue_named("4d").generator = generators.known(162)
        self.clue_named("6d").generator = generators.known(72)
        self.clue_named("9d").generator = generators.known(54)
        self.clue_named("12d").generator = generators.known(40)

        #2d
        self.clue_named("8a").generator = generators.known(12)
        self.clue_named("18d").generator = generators.known(51)
        self.clue_named("16a").generator = generators.known(30)

        # self.add_constraint("14d 16d 3a 9a", lambda a, b, c, d: amean(a, b) == gmean(c, d))
        self.clue_named("14d").generator = generators.known(378)
        self.clue_named("9a").generator = generators.known(529)

        self.add_constraint("15a 5a 11a 13a 5d 19d", lambda x, *y: int(x) == amean(*y))
        self.clue_named("15a").generator = generators.known(*range(100, 1000))
        self.clue_named("11a").generator = generators.known(*range(100, 1000))
        self.clue_named("13a").generator = generators.known(*range(100, 1000))
        self.clue_named("3d").generator = generators.known(*range(100, 1000))
        self.clue_named("5d").generator = generators.known(*range(1000, 10000))
        self.clue_named("15d").generator = generators.known(*range(100, 1000))

        self.add_constraint("14d 11a 3d 18d", lambda x, *y: int(x) == amean(*y))
        self.add_constraint("15d 16a 5d 12d 19d", lambda x, *y: int(x) == amean(*y))









if __name__ == '__main__':
    # run_me2()
    Magpie264.run()
