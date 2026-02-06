from __future__ import annotations

import itertools
import math
from collections.abc import Callable, Iterator, Iterable, Sequence
from typing import Union

from .clue import Clue

"""A collection of generators to use in various other puzzles."""
BASE = 10

ClueValueGenerator = Callable[[Clue], Iterable[Union[str, int]]]


def allvalues(clue: Clue) -> Iterable[int]:
    """All possible values that fit in the clue length"""
    min_value, max_value = get_min_max(clue)
    return iter(range(min_value, max_value))


def palindrome(clue: Clue) -> Iterator[str]:
    """Returns palindromes"""
    half_length = (clue.length + 1) // 2
    is_even = (clue.length & 1) == 0
    for i in range(BASE ** (half_length - 1), BASE ** half_length):
        left = str(i)
        right = left[::-1]
        yield left + (right if is_even else right[1:])


def square(clue: Clue) -> Iterator[int]:
    """Returns squares"""
    min_value, max_value = get_min_max(clue)
    lower = int(math.ceil(math.sqrt(min_value)))
    upper = int(math.ceil(math.sqrt(max_value)))
    return map(lambda x: x * x, range(lower, upper))


def cube(clue: Clue) -> Iterator[int]:
    """Returns cubes"""
    min_value, max_value = get_min_max(clue)
    lower = int(math.ceil(min_value ** (1 / 3)))
    upper = int(math.ceil(max_value ** (1 / 3)))
    return map(lambda x: x * x * x, range(lower, upper))


def sum_of_2_cubes(clue: Clue) -> Sequence[int]:
    min_value, max_value = get_min_max(clue)
    upper = int(math.ceil(max_value ** (1 / 3)))
    cubes = [x * x * x for x in range(1, upper)]
    sums = {sum(pair) for pair in itertools.combinations_with_replacement(cubes, 2)}
    result = sorted(x for x in sums if min_value <= x < max_value)
    return result

def filterer(predicate) -> Callable[[Clue], Iterable[int]]:
    def result(clue: Clue) -> Iterator[int]:
        min_value, max_value = get_min_max(clue)
        return filter(predicate, range(min_value, max_value))
    return result


def nth_power(n: int) -> Callable[[Clue], Iterable[int]]:
    def result(clue: Clue) -> Iterator[int]:
        min_value, max_value = get_min_max(clue)
        lower = int(math.ceil(min_value ** (1 / n)))
        upper = int(math.ceil(max_value ** (1 / n)))
        return map(lambda x: x ** n, range(lower, upper))
    return result


def prime(clue: Clue) -> Iterator[int]:
    """Returns primes"""
    return (p for p, is_prime in _prime_not_prime(clue) if is_prime)


def not_prime(clue: Clue) -> Iterator[int]:
    """Returns not primes"""
    return (p for p, is_prime in _prime_not_prime(clue) if not is_prime)


def _prime_not_prime(clue: Clue) -> Iterator[tuple[int, bool]]:
    """Returns (int, isPrime) for all integers of the right length"""
    min_value, max_value = get_min_max(clue)
    # Get list of the prime factors that could possibly divide our numbers
    max_factor = int(math.sqrt(max_value))
    factors = list(itertools.takewhile(lambda x: x <= max_factor, prime_generator()))

    for p in range(min_value, max_value):
        yield p, all(p % factor != 0 for factor in factors)


def known(*values: Union[int, str]) -> Callable[[Clue], Iterable[Union[int, str]]]:
    """Returns a fixed set of already known values"""
    return lambda _: values


def permutation(alphabet: str = '0123456789') -> Callable[[Clue], Iterator[str]]:
    """Returns a non-repeating permutation of digits from the alphabet"""

    def result(clue: Clue) -> Iterator[str]:
        permutations = itertools.permutations(alphabet, clue.length)
        return map(lambda x: ''.join(x), permutations)

    return result


def triangular(clue: Clue) -> Iterator[int]:
    """Returns triangular numbers"""
    return within_clue_limits(clue, (i * (i + 1) // 2 for i in itertools.count(1)))


def square_pyramidal_generator(clue: Clue) -> Iterator[int]:
    return within_clue_limits(clue,
                              itertools.accumulate(i * i for i in itertools.count(1)))


def fibonacci(clue: Clue) -> Iterator[int]:
    """Returns Fibonacci numbers"""
    return within_clue_limits(clue, __fibonacci_like(1, 2))


def lucas(clue: Clue) -> Iterator[int]:
    """Returns Lucas numbers"""
    return within_clue_limits(clue, __fibonacci_like(2, 1))


def within_clue_limits(clue: Clue, stream: Iterator[int]) -> Iterator[int]:
    """
    Filters a (possibly infinite) monotonically increasing Iterator so that it only
    returns those values that are within the limits of this clue.
    """
    min_value, max_value = get_min_max(clue)
    for value in stream:
        if value >= min_value:
            if value >= max_value:
                return
            yield value


def convert_to_base(num: int, base: int) -> str:
    """Converts a number to the specified base, and returns the value as a string"""
    result = []
    if not num:
        return '0'
    while num:
        num, mod = divmod(num, base)
        result.append('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz<>'[mod])
    result.reverse()
    return ''.join(result)


def using_current_base(generator: ClueValueGenerator) -> ClueValueGenerator:
    """
    Converts a ClueValueGenerator into a new ClueValueGenerator that converts all numeric
    input into strings of the specified base.  Needed when working with bases
    other than 10.
    """
    def result(clue: Clue) -> Iterator[str]:
        def maybe_convert(value: Union[int, str]) -> str:
            return value if isinstance(value, str) else convert_to_base(value, BASE)
        return map(maybe_convert, generator(clue))
    return result


def get_min_max(clue: Clue) -> tuple[int, int]:
    min_value = BASE ** (clue.length - 1)
    max_value = BASE * min_value
    return min_value, max_value


def prime_generator() -> Iterator[int]:
    yield from [2, 3, 5, 7]
    factor_sequence = prime_generator()
    next(factor_sequence)  # we don't need the 2, since we're only looking at odd numbers
    factors = [next(factor_sequence)]  # i.e. [3]
    while True:
        # The last element we pulled from factor_sequence was factors[-1]
        # We have generated all primes through factor[-1] ** 2 (which can't be a prime).
        next_factor = next(factor_sequence)
        # Let's look at all oee numbers through next_factor**2 (exclusive).
        # All composites must have at least one factor smaller than next_factor.
        for value in range((factors[-1] ** 2) + 2, next_factor ** 2, 2):
            if all(value % factor for factor in factors):
                yield value
        factors.append(next_factor)

#
# The following two aren't really used.  But they're a fun experiment that I was working
# on.  Making sure the recursion only goes one deep, by having everyone use the same list
# of factors.


def __prime2() -> Iterator[int]:
    yield from [2, 3, 5, 7]
    factors = [3]  # i.e. [3]
    factor_sequence = __prime2x(factors)
    for _ in range(1):
        next(factor_sequence)  # we don't need the 2, since we're only looking at odds
    while True:
        # The last element we pulled from factor_sequence was factors[-1]
        # We have generated all primes through factor[-1] ** 2 (which can't be a prime).
        next_factor = next(factor_sequence)
        # Let's look at all oee numbers through next_factor**2 (exclusive).
        # All composites must have at least one factor smaller than next_factor.
        for value in range((factors[-1] ** 2) + 2, next_factor ** 2, 2):
            if all(value % factor for factor in factors):
                yield value
        factors.append(next_factor)


def __prime2x(factors: list[int]) -> Iterator[int]:
    yield from [3, 5, 7]
    factor_count = 1
    while True:
        for value in range((factors[factor_count - 1] ** 2) + 2,
                           factors[factor_count] ** 2, 2):
            if all(value % factors[i] for i in range(factor_count)):
                yield value
        factor_count += 1


#
# end of code to ignore
#

def __fibonacci_like(start_i: int, start_j: int) -> Iterator[int]:
    i, j = start_i, start_j
    while True:
        yield i
        i, j = j, i + j


def phi(value: int) -> int:
    result = 1
    for prime in prime_generator():
        if value % prime == 0:
            value = value // prime
            count = 1
            while value % prime == 0:
                count += 1
                value = value // prime
            result *= count + 1
        if value == 1:
            return result
        if value < prime * prime:
            return result * 2
