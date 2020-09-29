import functools
import itertools
import math
import operator
import re
from collections import defaultdict, Counter
from typing import Sequence, Dict, Tuple, List, cast, Any, Union

from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse

from misc.primes import PRIMES
from solver import generators, ConstraintSolver, Clues, Clue, Location
from solver.constraint_solver import KnownClueDict
from solver.generators import filtering, allvalues


@functools.lru_cache(None)
def prime_factors(value: int) -> Sequence[Tuple[int, int]]:
    # 21033 is incorrect
    from misc.primes import PRIMES
    result = []
    for prime in PRIMES:
        if value % prime == 0:
            value = value // prime
            count = 1
            while value % prime == 0:
                count += 1
                value = value // prime
            result.append((prime, count))
        if value == 1:
            return result
        if value < prime * prime:
            result.append((value, 1))
            return result

@functools.lru_cache(None)
def divisor_count(value: int):
    factorization = prime_factors(value)
    return product(count + 1 for _prime, count in factorization)

def phi(value: int):
    # number of values that mutually prime
    current = value
    for prime, _ in  prime_factors(value):
        current = (current // prime) * (prime - 1)
    return current


@functools.lru_cache(None)
def factor_sum(value: int):
    factorization = prime_factors(value)
    return product((prime ** (count + 1) - 1) // (prime - 1) for prime, count in factorization)

@functools.lru_cache(None)
def factor_count(value: int) -> int:
    factorization = prime_factors(value)
    return product(count + 1 for _, count in factorization)


@functools.lru_cache(None)
def factor_list(value: int) -> Sequence[int]:
    def recurse(factor_list) -> Sequence[int]:
        if not factor_list:
            return [1]
        *start_factor_list, (prime, count) = factor_list
        sub_factors = recurse(start_factor_list)
        powers = [prime ** i for i in range(0, count + 1)]
        return [factor * power for factor in sub_factors for power in powers]

    result = sorted(recurse(prime_factors(value)))
    assert sum(result) == factor_sum(value)
    return result

@functools.lru_cache(None)
def shares_prime_factor(x, y):
    gcd = math.gcd(x, y)
    return gcd > 1

@functools.lru_cache(None)
def shared_factor_count(x, y) -> int:
    gcd = math.gcd(x, y)
    return factor_count(gcd)

@functools.lru_cache(None)
def odd_factor_count(value):
    while value % 2 == 0:
        value = value // 2
    return factor_count(value)

@functools.lru_cache(None)
def even_factor_count(value):
    try:
        if value & 1 == 1:
            return 0
        count = 0
        while value & 1 == 0:
            value = value // 2;
            count += 1
        return count * factor_count(value)
    except:
        print(value)

def product(values):
    return functools.reduce(operator.mul, values, 1)

GRID="""
XX.XX
X.X..
XX.X.
XX.XX
X.X..
"""

class Solver214(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver214()
        solver.verify_is_180_symmetric()
        solver.add_all_constraints()
        solver.solve(debug=True, max_debug_depth=50)
        # solver.solve()

    def __init__(self) -> None:
        super().__init__(self.get_clue_list())

    @staticmethod
    def get_clue_list() -> Sequence[Clue]:
        grid_locations = [None] + Clues.get_locations_from_grid(GRID)

        clues = [
            Clue("1a", True, grid_locations[1], 3, generator=filtering(lambda x: factor_count(x) == 6)),
            Clue("3a", True, grid_locations[3], 2, generator=allvalues),
            Clue("5a", True, grid_locations[5], 2, generator=filtering(lambda x: factor_count(factor_sum(x)) == 15)),
            Clue("6a", True, grid_locations[6], 3, generator=allvalues),
            Clue("8a", True, grid_locations[8], 3, generator=allvalues),
            Clue("10a", True, grid_locations[10], 3, generator=allvalues),
            Clue("12a", True, grid_locations[12], 2, generator=allvalues),
            Clue("14a", True, grid_locations[14], 2, generator=allvalues),
            Clue("15a", True, grid_locations[15], 3, generator=allvalues),

            Clue("1d", False, grid_locations[1], 2, generator=allvalues),
            Clue("2d", False, grid_locations[2], 3, generator=filtering(lambda x: factor_count(factor_sum(x)) == 16)),
            Clue("3d", False, grid_locations[3], 2, generator=allvalues),
            Clue("4d", False, grid_locations[4], 3, generator=allvalues),
            Clue("6d", False, grid_locations[6], 3, generator=allvalues),
            Clue("7d", False, grid_locations[7], 3, generator=generators.cube),
            Clue("9d", False, grid_locations[9], 3, generator=allvalues),
            Clue("11d", False, grid_locations[11], 2, generator=allvalues),
            Clue("13d", False, grid_locations[13], 2, generator=allvalues),
        ]
        return clues

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        special = self.clue_named("6d")
        special_count = factor_count(int(known_clues[special]))
        return all(special_count > factor_count(int(value)) for clue, value in known_clues.items() if clue != special)

    def add_all_constraints(self):
        self.add_constraint(("3a", "1a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("8a", "6d"), lambda x, y: even_factor_count(int(x)) > even_factor_count(int(y)))
        self.add_constraint(("10a", "12a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("12a", "1d"), lambda x, y: int(x) % int(y) == 0)
        self.add_constraint(("14a", "3a"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))
        self.add_constraint(("15a", "2d"), lambda x, y: shares_prime_factor(int(x), int(y)))
        self.add_constraint(("1d", "3d"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("4d", "13d"), lambda x, y: shared_factor_count(int(x), int(y)) > 5)
        # 6d will be handled in check_clue
        self.add_constraint(("13d", "3a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))

        self.add_constraint(("1a", "3a"), lambda x, y: even_factor_count(int(x)) == even_factor_count(int(y)))
        self.add_constraint(("5a", "6a"), lambda x, y: factor_sum(int(x)) == factor_sum(int(y)))
        self.add_constraint(("10a", "12a"), lambda x, y: odd_factor_count(int(x)) == odd_factor_count(int(y)))
        self.add_constraint(("14a", "15a"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))

        self.add_constraint(("1d", "7d"), lambda x, y: even_factor_count(int(x)) == even_factor_count(int(y)))
        self.add_constraint(("2d", "11d"), lambda x, y: factor_sum(int(x)) == factor_sum(int(y)))
        self.add_constraint(("3d", "9d"), lambda x, y: odd_factor_count(int(x)) == odd_factor_count(int(y)))
        self.add_constraint(("4d", "13d"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))




if __name__ == '__main__':
    Solver214.run()
    # temp = Solver214()



