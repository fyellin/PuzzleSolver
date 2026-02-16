import itertools
from typing import Unpack
from collections.abc import Sequence

from solver import Clue, ConstraintSolver, DrawGridArgs, Location, ClueValue
from solver import generators

CLUES = """
1 13?60 
2 41?90 
3 4?690 
4 ?68?0 
5 8717? 
6 4358?
7 ?146? 
8 ?65?0 
9 ?66?0
10 ?849? 
11 ?9?60 
12 ?95?0
13 ?3?50
14 351?? 
15 ??780 
16 ??890 
17 566?? 
18 491??
"""

primes = list(itertools.takewhile(lambda x: x < 1000, generators.prime_generator()))


class Solver208(ConstraintSolver):
    clue_primes: Sequence[tuple[int, int]]

    @staticmethod
    def run() -> None:
        solver = Solver208()
        solver.solve()

    def __init__(self) -> None:
        self.clue_primes = self.__get_clue_primes()
        clue_list = self.make_clue_list()
        super(Solver208, self).__init__(clue_list)

    def draw_grid(self, **args: Unpack[DrawGridArgs]) -> None:
        clue_values: dict[Clue, ClueValue] = args['clue_values']

        specials = self.__get_specials()
        shaded: set[Location] = set()
        for clue in self._clue_list:
            value = clue_values[clue]
            if int(value) in specials:
                shaded.update(clue.locations)
        shading = {x: 'yellow' for x in shaded}
        super().draw_grid(shading=shading, **args)

    def make_clue_list(self) -> list[Clue]:
        known = [value for _, value in self.clue_primes]
        generator = generators.known(*known)
        return [
            Clue('a', True, (1, 2), 2, generator=generator),
            Clue('b', True, (1, 4), 2, generator=generator),
            Clue('c', True, (2, 1), 2, generator=generator),
            Clue('d', True, (2, 3), 3, generator=generator),
            Clue('e', True, (3, 2), 3, generator=generator),
            Clue('f', True, (4, 1), 3, generator=generator),
            Clue('g', True, (4, 4), 2, generator=generator),
            Clue('h', True, (5, 1), 2, generator=generator),
            Clue('i', True, (5, 3), 2, generator=generator),

            Clue('j', False, (1, 1), 2, generator=generator),
            Clue('k', False, (1, 2), 3, generator=generator),
            Clue('l', False, (1, 4), 2, generator=generator),
            Clue('m', False, (2, 3), 3, generator=generator),
            Clue('n', False, (2, 5), 2, generator=generator),
            Clue('o', False, (3, 1), 2, generator=generator),
            Clue('p', False, (3, 4), 3, generator=generator),
            Clue('q', False, (4, 2), 2, generator=generator),
            Clue('r', False, (4, 5), 2, generator=generator),
        ]

    @classmethod
    def __get_clue_primes(cls) -> list[tuple[int, int]]:
        result = []
        for line in CLUES.splitlines():
            line = line.strip()
            if not line:
                continue
            fields = line.split(' ')
            clue_number = int(fields[0])
            clue_value = cls.__get_minimum_prime_non_factor(fields[1])
            result.append((clue_number, clue_value))
        print(result)
        return result

    @classmethod
    def __get_minimum_prime_non_factor(cls, pattern: str) -> int:
        temp = [pattern]
        for _ in range(pattern.count('?')):
            temp = [x.replace('?', i, 1) for i in "0123456789" for x in temp]
        values = [int(x) for x in temp if x[0] != '0']
        for prime in primes:
            if not any(value % prime == 0 for value in values):
                return prime
        assert False

    def __get_specials(self) -> Sequence[int]:
        primes_set = frozenset(primes)
        for items in itertools.combinations(self.clue_primes, 5):
            clue_info, clue_values = zip(*items)
            if sum(clue_values) != 315:
                continue
            if clue_info[0] in primes_set:
                continue
            if any(clue_info[i] not in primes_set for i in range(2, 5)):
                continue
            joined = ''.join(str(x) for x in clue_values)
            sum_digits = sum(int(x) for x in joined)
            if sum_digits != 27:
                continue
            print(list(zip(clue_info, clue_values)))
            return clue_values
        assert False


if __name__ == '__main__':
    Solver208.run()
