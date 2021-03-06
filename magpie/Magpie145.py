"""
Amusing puzzle, but all the work was in setting up the generators.  After that, it is straightforward
"""

import itertools
import re
from collections import defaultdict
from typing import Iterator, Mapping, Sequence, List

from solver import Clue, ConstraintSolver
from solver import generators


def fibonacci_generator() -> Iterator[int]:
    i, j = 1, 2
    while True:
        yield i
        i, j = j, i + j


primes = frozenset(itertools.takewhile(lambda x: x < 10000, generators.prime_generator()))
squares = frozenset(itertools.takewhile(lambda x: x < 10000, (i*i for i in itertools.count(1))))
cubes = frozenset(itertools.takewhile(lambda x: x < 10000, (i*i*i for i in itertools.count(1))))
fibonaccis = frozenset(itertools.takewhile(lambda x: x < 10000, fibonacci_generator()))


def set_up_table() -> Mapping[str, Sequence[int]]:
    temp = [''] * 10000
    result: Mapping[str, List[int]] = defaultdict(list)
    for i in range(1, 10000):
        q = i // 10
        value = temp[i] = temp[q] + str((i in primes) + (i in squares) + (i in cubes) + (i in fibonaccis))
        result[value].append(i)
    return result


MY_TABLE = set_up_table()


def make_clue_list(lines: str, acrosses: str, downs: str) -> List[Clue]:
    locations = [(0, 0)]
    for row, line in enumerate(lines.split()):
        for column, item in enumerate(line):
            if item == 'X':
                locations.append((row + 1, column + 1))
    clues = []
    for is_across, suffix, clue_info in ((True, 'a', acrosses), (False, 'd', downs)):
        for line in clue_info.split('\n'):
            if not line:
                continue
            match = re.fullmatch(r'(\d+) (\d+)', line)
            assert match
            number = int(match.group(1))
            info = match.group(2)
            clue = Clue(f'{number}{suffix}', is_across, locations[number], len(info),
                        generator=generators.known(*MY_TABLE[info]))
            clues.append(clue)
    return clues


GRID = """
XXXXXXX
X..X...
X.XX.XX
XXX.XX.
X..XX.X
X..X...
"""


ACROSS = """
1 0111
5 211
8 110
9 2011
10 11
11 201
13 11
15 30
17 212
19 11
20 1012
22 301
24 011
25 3002
"""


DOWN = """
1 01
2 111
3 021
4 21
5 201
6 302
7 00
10 10
12 20
14 21
16 101
17 211
18 210
19 102
20 10
21 01
23 20"""


def run() -> None:
    clue_list = make_clue_list(GRID, ACROSS, DOWN)
    solver = ConstraintSolver(clue_list)
    solver.verify_is_180_symmetric()
    solver.solve()


if __name__ == '__main__':
    run()
