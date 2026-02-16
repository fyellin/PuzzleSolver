import itertools
from collections import defaultdict
from collections.abc import Sequence
from functools import cache

from misc.factors import prime_factors, prime_factors_as_string
from solver import Clue, Clues, ConstraintSolver, generators, KnownClueDict

ACROSS_LENGTHS = "44/1111112/44/161/161/44/2111111/44"
DOWN_LENGTHS = "44/211111/44/161/161/44/1111112/44"

ACROSS = """
1 6 : 2
4 3 : 69
9 5 : 1
10 3 : 104
11 4 : 11
12 Unclued
14 Unclued
18 10 : 0
19 7 : 9
20 5 : 0
22 2 : 1427
23 6 : 4
"""

DOWN = """
1 4 : 16
2 2 : 2
3 10 : 1
5 11 : 0
6 2 : 594
7 Unclued
8 Unclued
13 3 : 1281
15 4 : 8
16 4 : 29
17 4 : 0
21 4 : 0
"""

def get_prime_info() -> dict[tuple[int, int], list[str]]:
    result = defaultdict(list)
    for i in range(10, 10_000):
        factors = prime_factors(i)
        count = sum(y for x, y in factors)
        delta = factors[-1][0] - factors[0][0]
        result[count, delta].append(i)
    return result

@cache
def get_anagram_multiples() -> dict[str, list[str]]:
    result = defaultdict(list)
    for i in range(100_000, 500_000):
        s = sorted(str(i))
        for multiple in range(2 * i, 1_000_000, i):
            if s == sorted(str(multiple)):
                result[str(i)].append(str(multiple))
    return result


class Listener4869(ConstraintSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self):
        self.prime_info = get_prime_info()
        self.anagram_multipliers = get_anagram_multiples()
        clue_list = self.get_clues()
        super().__init__(clue_list)

    def get_clues(self) -> Sequence[Clue]:
        clue_list = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        clue_dict = {clue.name: clue for clue in clue_list}
        for info in (ACROSS, DOWN):
            across = info is ACROSS
            for line in info.strip().splitlines():
                pieces = line.strip().split()
                clue = clue_dict[f'{pieces[0]}{"a" if across else "d"}']
                if len(pieces) == 2:
                    assert pieces[1] == "Unclued"
                    clue.generator = generators.known(*self.anagram_multipliers.keys())
                else:
                    assert pieces[2] == ':'
                    count, delta = int(pieces[1]), int(pieces[3])
                    clue.generator = generators.known(*self.prime_info[count, delta])
        return clue_list

    def show_solution(self, known_clues: KnownClueDict) -> None:
        result = {clue.name: value for clue, value in known_clues.items()}
        print(result)
        Listener4869b.run(result)
        super().show_solution(known_clues)

class Listener4869b(ConstraintSolver):
    @classmethod
    def run(cls, clue_values: dict[str, str]):
        solver = cls(clue_values)
        solver.solve(debug=False)

    def __init__(self, clue_values):
        self.anagram_multipliers = get_anagram_multiples()
        self.original_clue_values = clue_values
        clue_list = self.get_clues(clue_values)
        super().__init__(clue_list)

    def get_clues(self, clue_values: dict[str, str]) -> Sequence[Clue]:
        clue_list = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        all_old_clues = set(clue_values.values())
        for clue in clue_list:
            original_value = clue_values[clue.name]
            if clue.name in ('7d', '8d', '12a', '14a'):
                anagrams = set(self.anagram_multipliers[original_value])
            else:
                anagrams = {''.join(x) for x in itertools.permutations(original_value)
                            if x[0] != '0'}
            anagrams -= all_old_clues
            clue.generator = generators.known(*anagrams)
        return clue_list

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        assert len(known_clues.values()) == len(set(known_clues.values()))
        assert len(self.original_clue_values.values()) == len(set(self.original_clue_values.values()))
        return set(known_clues.values()).isdisjoint(set(self.original_clue_values.values()))

    def show_solution(self, known_clues: KnownClueDict) -> None:
        for clue in sorted(
                self._clue_list, key=lambda x: (not x.is_across, x.locations[0])):
            old_value = self.original_clue_values[clue.name]
            new_value = known_clues[clue]
            if clue.name not in ('7d', '8d', '12a', '14a'):
                print(f'{clue.name:3}: {old_value:>6} = '
                      f'{prime_factors_as_string(int(old_value), separator="×")}')
            else:
                q, r = divmod(int(new_value), int(old_value))
                assert r == 0
                print(f'{clue.name:3}: {old_value:} * {q} = {new_value}')

        super().show_solution(known_clues)


if __name__ == '__main__':
    Listener4869.run()
