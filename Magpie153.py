import itertools
from typing import Iterator, Mapping, Dict, FrozenSet, Sequence, Tuple, Optional, List, Iterable, Callable

import Generators
from Clue import Clue, ClueList, ClueValue, ClueValueGenerator
from GenericSolver import SolverByClue

"""
A decomposition n = a^2 - b^2 = (a-b)(a+b) = d*(n/d) is given for each divisor d less than
(as to exclude b = 0) but having the same parity as n/d. For even n this implies that d and n/d must be
even, i.e., 4 | n.
This leads to the given formula, a(n) = floor(numdiv(n)/2) for odd n, floor(numdiv(n/4)/2) for n = 4k, 0
else. - M. F. Hasler, Jul 10 2018

R:  if x is odd     floor(factors(x) / 2)
    if x is mod 4   floor(factors(x/4) / 2)
    if x otherwise  none

S.  Pull out all factors of 2.  factors(q) - 1, to remove singleton sequence

Pull out all factors of 2.  Number of factors of that.  Subtract 1 to remove singleton sequence
"""


def set_up_tables() -> Tuple[Sequence[int], Sequence[int], Sequence[int], Sequence[int]]:
    max_value = 100_000
    primes = tuple(itertools.takewhile(lambda x: x < max_value, Generators.prime_generator()))
    primes_set = set(primes)

    prime_info = [(1, 1, 0)] * max_value
    prime_count = [0] * max_value
    factor_count = [0] * max_value
    rsequence_count = [0] * max_value  # R
    square_count = [0] * max_value  # S

    factor_count[1] = 1
    for value in range(2, max_value):
        if value in primes_set:
            multiplier, smallest_prime, exponent = 1, value, 1  # 1 * value ^ 1
        else:
            smallest_prime = next(i for i in primes if value % i == 0)
            parent = value // smallest_prime
            p_multiplier, p_smallest_prime, p_exponent = prime_info[parent]
            if smallest_prime == p_smallest_prime:
                multiplier, exponent = p_multiplier, p_exponent + 1
            else:
                multiplier, exponent = parent, 1
        prime_info[value] = multiplier, smallest_prime, exponent
        prime_count[value] = prime_count[multiplier] + 1
        factor_count[value] = factor_count[multiplier] * (exponent + 1)
        rsequence_count[value] = factor_count[value] - 1 if value % 2 else rsequence_count[value // 2]
        if value % 2:
            square_count[value] = factor_count[value] // 2
        elif value % 4:
            square_count[value] = 0
        else:
            square_count[value] = factor_count[value // 4] // 2
    return prime_count, factor_count, rsequence_count, square_count


pp, ff, rr, ss = set_up_tables()


def show_items(*, P: Optional[int] = None, F: Optional[int] = None, R: Optional[int] = None, S: Optional[int] = None) \
        -> Callable[[Clue], Iterable[int]]:
    def generator(clue: Clue) -> Iterable[int]:
        items: Iterable[int] = range(10 ** (clue.length - 1), 10 ** clue.length)
        if P:
            items = filter(lambda x: pp[x] == P, items)
        if R:
            items = filter(lambda x: rr[x] == R, items)
        if F:
            items = filter(lambda x: ff[x] == F, items)
        if S:
            items = filter(lambda x: ss[x] == S, items)
        return items

    return generator


def make_clue_list(lines: str,
                   acrosses: Sequence[Tuple[int, int, ClueValueGenerator]],
                   downs: Sequence[Tuple[int, int, ClueValueGenerator]]) -> List[Clue]:
    locations = [(0, 0)]
    for row, line in enumerate(lines.split()):
        for column, item in enumerate(line):
            if item == 'X':
                locations.append((row + 1, column + 1))
    clues = []
    for is_across, suffix, clue_set in ((True, 'a', acrosses), (False, 'd', downs)):
        for (location, length, generator) in clue_set:
            clue = Clue.make(f'{location}{suffix}', is_across, locations[location], length, generator=generator)
            clues.append(clue)
    return clues


def generate_1a(clue: Clue) -> Iterable[int]:
    min_value = 10 ** (clue.length - 1)
    max_value = 10 ** clue.length
    return range(min_value + 2, max_value, 4)


def generate_35a(clue: Clue) -> Iterator[int]:
    min_value = 10 ** (clue.length - 1)
    max_value = 10 ** clue.length
    return (x for x in range(min_value, max_value) if ss[x] == rr[x] + 2)


def generate_17d18d(min_power: int) -> Callable[[Clue], Iterable[int]]:
    def generator(clue: Clue) -> Iterator[int]:
        min_value = 10 ** (clue.length - 1)
        max_value = 10 ** clue.length
        primes = Generators.prime_generator()
        for prime in primes:
            for power in itertools.count(min_power):
                result = prime ** power
                if result >= min_value:
                    if result >= max_value:
                        if power == min_power:
                            return
                        break
                    yield result

    return generator


def generate_5d(clue: Clue) -> Iterator[int]:
    min_value = 10 ** (clue.length - 1)
    max_value = 10 ** clue.length
    return (x for x in range(min_value, max_value)
            if rr[x] < 3 and pp[x] == 2 and ff[x] == 9 * rr[x] + 9)


GRID = """
XXXXXX.X
.X.X..X.
X..X.X..
X.X.XX..
XX....X.
X.XXX...
XX..X.XX
X.XX.X..
X....X..
.X......"""

CLUES = make_clue_list(GRID,
                       ((1, 7, generate_1a),
                        (8, 2, Generators.allvalues),
                        (9, 5, Generators.allvalues),
                        (11, 3, show_items(P=3, R=3, S=4)),
                        (12, 2, show_items(P=2)),
                        (13, 3, show_items(P=1)),
                        (14, 4, Generators.allvalues),
                        (16, 4, Generators.allvalues),
                        (19, 5, show_items(P=1, R=3)),
                        (20, 2, Generators.allvalues),
                        (21, 2, Generators.allvalues),
                        (22, 5, show_items(F=20, P=2, R=1)),
                        (25, 4, Generators.allvalues),
                        (27, 4, Generators.allvalues),
                        (30, 3, Generators.allvalues),
                        (32, 2, show_items(R=3)),
                        (33, 3, Generators.allvalues),
                        (34, 5, show_items(P=2)),
                        (35, 2, generate_35a),
                        (36, 7, Generators.known(2 ** 20, 2 ** 21, 2 ** 22, 2 ** 23))),
                       ((1, 4, Generators.allvalues),
                        (2, 4, show_items(F=16, P=3, R=3, S=4)),
                        (3, 3, show_items(F=6, S=0)),
                        (4, 5, Generators.allvalues),
                        (5, 3, generate_5d),
                        (6, 3, show_items(F=18, P=3, S=0)),
                        (7, 6, Generators.allvalues),
                        (10, 3, show_items(P=1)),
                        (15, 4, Generators.allvalues),
                        (16, 2, show_items(P=1)),
                        (17, 4, generate_17d18d(2)),
                        (18, 6, generate_17d18d(5)),
                        (19, 2, Generators.allvalues),
                        (20, 2, Generators.allvalues),
                        (23, 2, Generators.allvalues),
                        (24, 5, show_items(F=32, P=3, S=0)),
                        (26, 3, show_items(S=3)),
                        (28, 4, show_items(F=54, P=4)),
                        (29, 4, show_items(F=18, P=2)),
                        (31, 3, Generators.allvalues),
                        (32, 3, show_items(R=7, S=0)),
                        (33, 3, Generators.allvalues)))


class MySolver(SolverByClue):
    def __init__(self, cl: ClueList):
        super(MySolver, self).__init__(cl)
        (self.a1, self.a8, self.a9, self.a11, self.a12, self.a13, self.a14, self.a16, self.a19,
         self.a20, self.a21, self.a22, self.a25, self.a27, self.a30, self.a32, self.a33, self.a34,
         self.a35, self.a36,
         self.d1, self.d2, self.d3, self.d4, self.d5, self.d6, self.d7, self.d10, self.d15, self.d16,
         self.d17, self.d18, self.d19, self.d20, self.d23, self.d24, self.d26, self.d28, self.d29,
         self.d31, self.d32, self.d33) = list(cl.iterator())

    def post_clue_assignment_fixup(self, clue: Clue, known_clues: Mapping[Clue, ClueValue],
                                   unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:

        def is_factor_of(clue1: Clue, clue2: Clue) -> bool:
            if clue == clue1 or clue == clue2:
                return self.check_2_clue_relationship(clue1, clue2, unknown_clues, lambda x, y: int(y) % int(x) == 0)
            else:
                return True

        result = all(is_factor_of(clue1, clue2) for (clue1, clue2) in (
            (self.a8,  self.a9),
            (self.a16, self.a14),
            (self.a20, self.a9),
            (self.a20, self.a21),
            (self.a21, self.d1),
            (self.a30, self.d1),
            (self.a33, self.a27),
            (self.d7,  self.a1),
            (self.d16, self.d15),
            (self.d19, self.d2),
            (self.d19, self.d4),
            (self.d20, self.d23),
            (self.d26, self.a25),
            (self.d31, self.a34),
            (self.d31, self.d4)))
        if result and clue in (self.a30, self.d33, self.d24):
            result = self.check_n_clue_relationship(
                (self.a30, self.d33, self.d24), unknown_clues, lambda a, b, c: int(a) * int(b) == int(c))
        return result

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        self.clue_list.plot_board(known_clues)
        print('************************')


def run():
    clue_list = ClueList.create(CLUES)
    clue_list.verify_is_180_symmetric()
    solver = MySolver(clue_list)
    solver.solve(debug=True)


if __name__ == '__main__':
    run()
