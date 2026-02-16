"""
Two solvers, one inside the other.
The first solver is needed just to generate a list of numbers.  It has two special features:
    Answers are generated in numeric order
    All answers must be p^5 or pq^2
    They are not laid out in a grid.
"""

import functools
import itertools
import re
from collections.abc import Sequence, Iterable, Callable

from solver import Clue, ClueValue, ConstraintSolver, EquationSolver, Intersection
from solver import generators
# 6  4s
# 14 5s
# 6  6s
# 4  7s
from solver import KnownClueDict, KnownLetterDict

CLUE_DATA = """
1 4 DDS
2 4 A(T + (O – T)(A – L))(T + (O – T)(A – L))
3 4 A((R + O)U – N – D)((R + O)U – N – D)
4 4 A(W + H + O + L + E)(W + H + O + L + E)
5 4 S((R + O)U – N – D)((R + O)U – N – D)
6 4 A(SE(N + A) + R – Y)(SE(N + A) + R – Y)
7 5 A(S – (E + X – T)(E – T))(S – (E + X – T)(E – T))
8 5 S(BAS – E)(BAS – E)
9 5 U(S – (E + X – T)(E – T))(S – (E + X – T)(E – T))
10 5 U(BAS + E)(BAS + E)
11 5 A(N + U(M + B + E) – R)(N + U(M + B + E) – R)
12 5 YY((MO + D)(U + L) + O)
13 5 S(T – (O – TA)L)(T – (O – TA)L)
14 5 UU(D(I + V + I)S + O + R)
15 5 SS(FA(CT – O) + R)
16 5 Y(S + (E + X – T)(E + T))(S + (E + X – T)(E + T))
17 5 (H – E + X – A + D)(F + W)(F + W)
18 5 (H + Q)(H + Q)((R + O)U – N – D)
19 5 RR((CA + N)C – E – L)
20 5 RR(A – L(I – Q)UO + T)
21 6 (K + W)(B(A + S) – E)(B(A + S) – E)
22 6 AE((P + R)I – M + E)((P + R)I – M + E)
23 6 ((P/O)W + E + R)(CU + T)(CU + T)
24 6 (W + X)(W + X)(D(E + C + I – M) – AL)
25 6 Z(D – I – G + IT)(D – I – G + IT)
26 6 R((D – I/V)I + DE)((D – I/V)I + DE)
27 7 (T – E – N)QQQQQ
28 7 (S – A)NNNNN
29 7 (TJ + E)(SHA + RE)(SHA + RE)
30 7 (L – S)DDDDD
"""


def make_clue_list(info: str) -> Sequence[Clue]:
    clues = []
    for line in info.splitlines():
        if not line:
            continue
        match = re.fullmatch(r'(\d+) (\d) (.*)', line)
        assert match
        # We don't care about the location.  We just care about the length
        clue = Clue(match.group(1), True, (1, 1), int(match.group(2)), expression=match.group(3))
        clues.append(clue)
    return clues


primes = list(itertools.takewhile(lambda x: x * x < 10_000_000, generators.prime_generator()))
primes_set = frozenset(primes)
squares_set = frozenset(i * i for i in primes)


@functools.lru_cache(maxsize=None)
def is_legal_value(clue_value: ClueValue) -> bool:
    value = int(clue_value)
    if not 1000 <= value <= 9_999_999:
        return False
    factor = next((p for p in primes if value % p == 0), None)
    if not factor:
        return False
    if factor ** 5 == value:
        return True
    temp = value // factor
    if temp % factor == 0:
        temp = temp // factor
        if temp <= primes[-1]:
            return temp != factor and temp in primes_set
        else:
            return all(temp % p != 0 for p in primes)
    else:
        return temp in squares_set


class OuterSolver(EquationSolver):
    @staticmethod
    def run() -> None:
        clue_list = make_clue_list(CLUE_DATA)
        solver = OuterSolver(clue_list)
        solver.solve()

    def __init__(self, clues: Sequence[Clue]):
        super().__init__(clues, items=range(1, 27))
        for clue in clues:
            self.add_constraint((clue,), lambda x: is_legal_value(x))
        for clue1, clue2 in itertools.combinations(clues, 2):
            assert int(clue1.name) < int(clue2.name)
            if clue1.length == clue2.length:
                self.add_constraint((clue1, clue2), lambda x, y: int(x) < int(y))

    def make_pattern_generator(self, clue: Clue, intersections: Sequence[Intersection]) -> \
            Callable[[KnownClueDict], re.Pattern[str]]:
        pattern_string = f'.{{{clue.length}}}'   # e.g.  r'.{5}' if clue.length == 5.
        pattern = re.compile(pattern_string)
        return lambda _: pattern

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        super().show_letter_values(known_letters)
        answers = tuple(known_clues.values())
        InnerSolver.run(answers)


ACROSS = [(11, 5), (16, 5), (21, 4), (25, 5), (34, 7), (41, 5), (55, 6), (61, 6), (76, 5), (81, 7),
          (92, 5), (97, 4), (101, 5), (106, 5)]
DOWN = [(11, 5), (12, 4), (13, 7), (15, 4), (16, 5), (17, 6), (19, 6), (20, 5), (48, 7), (52, 6),
        (54, 6), (61, 5), (65, 5), (70, 5), (76, 4), (79, 4)]


class InnerSolver(ConstraintSolver):
    @staticmethod
    def run(entries: Sequence[ClueValue]) -> None:
        def generator(a_clue: Clue) -> Iterable[str]:
            return (entry for entry in entries if len(entry) == a_clue.length)

        clues = []
        for suffix, is_across, clue_info in (('a', True, ACROSS), ('d', False, DOWN)):
            for xy, length in clue_info:
                q, r = divmod(xy - 11, 10)
                clue = Clue(f'{xy}{suffix}', is_across, (q + 1, r + 1), length, generator=generator)
                clues.append(clue)
        solver = InnerSolver(clues)
        solver.solve()


if __name__ == '__main__':
    OuterSolver.run()

