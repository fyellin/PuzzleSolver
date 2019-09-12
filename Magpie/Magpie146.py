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
from datetime import datetime
from operator import itemgetter
from typing import Dict, Sequence, Tuple, List, Set, Iterable, Any

import Generators
from Clue import ClueList, Letter, ClueValue, Clue
from GenericSolver import ConstraintSolver

CLUE_DATA = """
1 DDS
2 A(T + (O – T)(A – L))(T + (O – T)(A – L))
3 A((R + O)U – N – D)((R + O)U – N – D)
4 A(W + H + O + L + E)(W + H + O + L + E)
5 S((R + O)U – N – D)((R + O)U – N – D)
6 A(SE(N + A) + R – Y)(SE(N + A) + R – Y)
7 A(S – (E + X – T)(E – T))(S – (E + X – T)(E – T))
8 S(BAS – E)(BAS – E)
9 U(S – (E + X – T)(E – T))(S – (E + X – T)(E – T))
10 U(BAS + E)(BAS + E)
11 A(N + U(M + B + E) – R)(N + U(M + B + E) – R)
12 YY((MO + D)(U + L) + O)
13 S(T – (O – TA)L)(T – (O – TA)L)
14 UU(D(I + V + I)S + O + R)
15 SS(FA(CT – O) + R)
16 Y(S + (E + X – T)(E + T))(S + (E + X – T)(E + T))
17 (H – E + X – A + D)(F + W)(F + W)
18 (H + Q)(H + Q)((R + O)U – N – D)
19 RR((CA + N)C – E – L)
20 RR(A – L(I – Q)UO + T)
21 (K + W)(B(A + S) – E)(B(A + S) – E)
22 AE((P + R)I – M + E)((P + R)I – M + E)
23 ((P/O)W + E + R)(CU + T)(CU + T)
24 (W + X)(W + X)(D(E + C + I – M) – AL)
25 Z(D – I – G + IT)(D – I – G + IT)
26 R((D – I/V)I + DE)((D – I/V)I + DE)
27 (T – E – N)QQQQQ
28 (S – A)NNNNN
29 (TJ + E)(SHA + RE)(SHA + RE)
30 (L – S)DDDDD"""


def make_clue_list(info: str) -> ClueList:
    clues = []
    for line in info.splitlines():
        if not line:
            continue
        match = re.fullmatch(r'(\d+) (.*)', line)
        assert match
        clue = Clue(match.group(1), True, (1, 1), 1, expression=match.group(2))
        clues.append(clue)
    return ClueList(clues)


primes = list(itertools.takewhile(lambda x: x * x < 10_000_000, Generators.prime_generator()))
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


class Magpie146Solver:
    clue_list: ClueList
    count_total: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_order: Sequence[Any]
    debug: bool

    def __init__(self, clue_list: ClueList) -> None:
        self.clue_list = clue_list

    def solve(self, *, show_time: bool = True, debug: bool = False) -> None:
        self.count_total = 0
        self.known_letters = {}
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        self.solving_order = self._get_solving_order()
        time2 = datetime.now()
        self.__solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Steps: {self.count_total}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_order):
            self.show_solution(self.known_clues, self.known_letters)
            return
        (clue, clue_letters, (min_clue, max_clue)) = self.solving_order[current_index]
        min_value = int(self.known_clues[min_clue]) if min_clue else 999
        max_value = int(self.known_clues[max_clue]) if max_clue else 10_000_000
        try:
            for next_letter_values in self.get_letter_values(self.known_letters, len(clue_letters)):
                self.count_total += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                evaluator, _ = clue.evaluators[0]
                clue_value = evaluator(self.known_letters)
                if not clue_value or not is_legal_value(clue_value):
                    continue
                if not min_value < int(clue_value) < max_value:
                    continue

                def show_it(info: str) -> None:
                    if self.debug:
                        print(f'{" | " * current_index} {clue.name} {clue_letters} '
                              f'{next_letter_values} {clue_value} ({clue.length}): {info}')

                self.known_clues[clue] = clue_value
                show_it('--->')
                self.__solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            self.known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[Any]:
        """Figures out the best order to solve the various clues."""
        result: List[Any] = []
        not_yet_ordered: Dict[Clue, Tuple[Clue, Set[Letter]]] = {
            # Each clue has only one evaluator, so using clue as the key is fine.
            clue: (clue, set(evaluator_vars)) for clue in self.clue_list for (_, evaluator_vars) in clue.evaluators
        }

        def evaluator(item: Tuple[Clue, Set[Letter]]) -> Sequence[int]:
            # Largest value wins.  Precedence is given to the clue with the least number of unknown variables.
            # Within that, ties are broken by the longest clue length, so we create the most intersections
            clue, clue_unknown_letters = item
            return -len(clue_unknown_letters), clue.length

        while not_yet_ordered:
            clue, unknown_letters = max(not_yet_ordered.values(), key=evaluator)
            not_yet_ordered.pop(clue)
            less = [seen_clue for (seen_clue, _, _) in result if int(seen_clue.name) < int(clue.name)]
            more = [seen_clue for (seen_clue, _, _) in result if int(seen_clue.name) > int(clue.name)]
            less_clue = None if not less else max(less, key=lambda x: int(x.name))
            more_clue = None if not more else min(more, key=lambda x: int(x.name))
            result.append((clue, tuple(sorted(unknown_letters)), (less_clue, more_clue)))
            for (other_clue, other_unknown_letters) in not_yet_ordered.values():
                other_unknown_letters.difference_update(unknown_letters)
        return tuple(result)

    @staticmethod
    def get_letter_values(known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        known_values = set(known_letters.values())
        not_set_values = [i for i in range(1, 27) if i not in known_values]
        return itertools.permutations(not_set_values, count)

    def show_solution(self, known_clues: Dict[Clue, ClueValue], known_letters: Dict[Letter, int]) -> None:
        answers = tuple(known_clues.values())
        # self.clue_list.print_board(self.known_clues)
        print()
        pairs = [(letter, value) for letter, value in known_letters.items()]
        pairs.sort()
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))
        run2(answers)


def run() -> None:
    clue_list = make_clue_list(CLUE_DATA)
    solver = Magpie146Solver(clue_list)
    solver.solve()


ACROSS = [(11, 5), (16, 5), (21, 4), (25, 5), (34, 7), (41, 5), (55, 6), (61, 6), (76, 5), (81, 7),
          (92, 5), (97, 4), (101, 5), (106, 5)]
DOWN = [(11, 5), (12, 4), (13, 7), (15, 4), (16, 5), (17, 6), (19, 6), (20, 5), (48, 7), (52, 6),
        (54, 6), (61, 5), (65, 5), (70, 5), (76, 4), (79, 4)]


def run2(entries: Sequence[ClueValue]) -> None:
    def generator(a_clue: Clue) -> Iterable[str]:
        return (entry for entry in entries if len(entry) == a_clue.length)

    clues = []
    for suffix, is_across, clue_info in (('a', True, ACROSS), ('d', False, DOWN)):
        for xy, length in clue_info:
            q, r = divmod(xy - 11, 10)
            clue = Clue(f'{xy}{suffix}', is_across, (q + 1, r + 1), length, generator=generator)
            clues.append(clue)
    clue_list = ClueList(clues)
    solver = ConstraintSolver(clue_list)
    solver.solve()


if __name__ == '__main__':
    run()

