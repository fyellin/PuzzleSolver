import itertools
import math
import string
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator, Sequence

from more_itertools import sieve

from .clue import Clue

"""A collection of generators to use in various other puzzles."""
BASE = 10

ClueValueGenerator = Callable[[Clue], Iterable[str | int]]


def allvalues(clue: Clue) -> Iterable[int]:
    """All possible values that fit in the clue length"""
    min_value, max_value = get_min_max(clue)
    return range(min_value, max_value)


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
    lower = math.ceil(math.sqrt(min_value))
    upper = math.ceil(math.sqrt(max_value))
    return (x * x for x in range(lower, upper))


def cube(clue: Clue) -> Iterator[int]:
    """Returns cubes"""
    min_value, max_value = get_min_max(clue)
    lower = math.ceil(min_value ** (1 / 3))
    upper = math.ceil(max_value ** (1 / 3))
    return (x * x * x for x in range(lower, upper))


def sum_of_2_cubes(clue: Clue) -> Sequence[int]:
    min_value, max_value = get_min_max(clue)
    upper = math.ceil(max_value ** (1 / 3))
    cubes = [x * x * x for x in range(1, upper)]
    sums = {sum(pair) for pair in itertools.combinations_with_replacement(cubes, 2)}
    return sorted(x for x in sums if min_value <= x < max_value)


def filterer(predicate: Callable[[int], bool]) -> Callable[[Clue], Iterable[int]]:
    def result(clue: Clue) -> Iterator[int]:
        min_value, max_value = get_min_max(clue)
        return filter(predicate, range(min_value, max_value))
    return result


def nth_power(n: int) -> Callable[[Clue], Iterable[int]]:
    def result(clue: Clue) -> Iterator[int]:
        min_value, max_value = get_min_max(clue)
        lower = math.ceil(min_value ** (1 / n))
        upper = math.ceil(max_value ** (1 / n))
        return (x ** n for x in range(lower, upper))
    return result


def prime(clue: Clue) -> Iterator[int]:
    """Returns primes"""
    min_value, max_value = get_min_max(clue)
    return itertools.dropwhile(lambda x: x < min_value, sieve(max_value))


def not_prime(clue: Clue) -> Iterator[int]:
    """Returns composites"""
    min_value, max_value = get_min_max(clue)
    primes = sieve(max_value)
    while (next_prime := next(primes, max_value)) <= min_value:
        pass
    for i in range(min_value, max_value):
        if i == next_prime:
            next_prime = next(primes, max_value)
        else:
            yield i


def known[T: (int, str)](*values: T) -> Callable[[Clue], Iterable[T]]:
    """Returns a fixed set of already known values"""
    return lambda _: values


def permutation(alphabet: str = string.digits) -> Callable[[Clue], Iterator[str]]:
    """Returns a non-repeating permutation of digits from the alphabet"""

    def result(clue: Clue) -> Iterator[str]:
        permutations = itertools.permutations(alphabet, clue.length)
        return map(''.join, permutations)

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
    """Converts a number to the specified base and returns the value as a string"""
    result = []
    if not num:
        return '0'
    while num:
        num, mod = divmod(num, base)
        result.append('0123456789'
                      'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
                      'abcdefghijklmnopqrstuvwxyz<>'[mod])
    result.reverse()
    return ''.join(result)


def using_current_base(generator: ClueValueGenerator) -> ClueValueGenerator:
    """
    Converts a ClueValueGenerator into a new ClueValueGenerator that converts all numeric
    input into strings of the specified base.  Needed when working with bases
    other than 10.
    """
    def result(clue: Clue) -> Iterator[str]:
        def maybe_convert(value: int | str) -> str:
            return value if isinstance(value, str) else convert_to_base(value, BASE)
        return map(maybe_convert, generator(clue))
    return result


def get_min_max(clue: Clue) -> tuple[int, int]:
    min_value = BASE ** (clue.length - 1)
    max_value = BASE * min_value
    return min_value, max_value


def prime_generator(max_value: int, primes: bool = True):
    max_witness = math.isqrt(max_value)
    composite_witnesses = defaultdict(list)
    yield 2
    for i in range(3, max_value, 2):
        if i not in composite_witnesses:
            if primes:
                yield i
            if i <= max_witness:
                composite_witnesses[i * i].append(i)
        else:
            if not primes:
                yield i
            for witness in composite_witnesses.pop(i):
                composite_witnesses[i + 2 * witness].append(witness)


def __fibonacci_like(start_i: int, start_j: int) -> Iterator[int]:
    i, j = start_i, start_j
    while True:
        yield i
        i, j = j, i + j
