import functools
import math
import operator
from typing import Sequence, Tuple, Iterator


@functools.cache
def prime_factors(value: int) -> Sequence[Tuple[int, int]]:
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


@functools.cache
def divisor_count(value: int) -> int:
    factorization = prime_factors(value)
    return product(count + 1 for _prime, count in factorization)


def phi(value: int) -> int:
    # number of values that mutually prime
    current = value
    for prime, _ in prime_factors(value):
        current = (current // prime) * (prime - 1)
    return current


@functools.cache
def factor_sum(value: int) -> int:
    factorization = prime_factors(value)
    return product((prime ** (count + 1) - 1) // (prime - 1) for prime, count in factorization)


@functools.cache
def factor_count(value: int) -> int:
    factorization = prime_factors(value)
    return product(count + 1 for _, count in factorization)


@functools.cache
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


@functools.cache
def shared_factor_count(x: int, y: int) -> int:
    gcd = math.gcd(x, y)
    return factor_count(gcd)


@functools.cache
def odd_factor_count(value: int) -> int:
    while value % 2 == 0:
        value = value // 2
    return factor_count(value)


@functools.cache
def even_factor_count(value: int) -> int:
    count = 0
    while value & 1 == 0:
        value = value // 2
        count += 1
    return 0 if count == 0 else count * factor_count(value)


def product(values: Iterator[int]) -> int:
    return functools.reduce(operator.mul, values, 1)

superscript_mapping = str.maketrans({
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹"
})
subscript_mapping = str.maketrans({
    "0": "₀",
    "1": "₁",
    "2": "₂",
    "3": "₃",
    "4": "₄",
    "5": "₅",
    "6": "₆",
    "7": "₇",
    "8": "₈",
    "9": "₉"
})

def prime_factors_as_string(value: int, show_one=False, separator='·') -> str:
    results = []
    for prime, count in prime_factors(value):
        if count == 1 and not show_one:
            results.append(str(prime))
        else:
            results.append(f"{prime}{str(count).translate(superscript_mapping)}")
    return separator.join(results)


if __name__ == '__main__':
    for x in (5662, 5663, 5664, 5665, 6661, 6663, 6664, 6666):
        print(prime_factors_as_string(x))
