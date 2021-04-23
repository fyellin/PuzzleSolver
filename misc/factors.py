import functools
import math
import operator
from typing import Sequence, Tuple, Iterator


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
def divisor_count(value: int) -> int:
    factorization = prime_factors(value)
    return product(count + 1 for _prime, count in factorization)


def phi(value: int) -> int:
    # number of values that mutually prime
    current = value
    for prime, _ in prime_factors(value):
        current = (current // prime) * (prime - 1)
    return current


@functools.lru_cache(None)
def factor_sum(value: int) -> int:
    factorization = prime_factors(value)
    return product((prime ** (count + 1) - 1) // (prime - 1) for prime, count in factorization)


@functools.lru_cache(None)
def factor_count(value: int) -> int:
    factorization = prime_factors(value)
    return product(count + 1 for _, count in factorization)


@functools.lru_cache(None)
def factor_list(value: int) -> Sequence[int]:
    def recurse(prime_factor_list) -> Sequence[int]:
        if not prime_factor_list:
            return [1]
        *start_factor_list, (prime, count) = prime_factor_list
        sub_factors = recurse(start_factor_list)
        powers = [prime ** i for i in range(0, count + 1)]
        return [factor * power for factor in sub_factors for power in powers]

    result = sorted(recurse(prime_factors(value)))
    assert sum(result) == factor_sum(value)
    return result


@functools.lru_cache(None)
def shared_factor_count(x: int, y: int) -> int:
    gcd = math.gcd(x, y)
    return factor_count(gcd)


@functools.lru_cache(None)
def odd_factor_count(value: int) -> int:
    while value % 2 == 0:
        value = value // 2
    return factor_count(value)


@functools.lru_cache(None)
def even_factor_count(value: int) -> int:
    count = 0
    while value & 1 == 0:
        value = value // 2
        count += 1
    return 0 if count == 0 else count * factor_count(value)


def product(values: Iterator[int]) -> int:
    return functools.reduce(operator.mul, values, 1)
