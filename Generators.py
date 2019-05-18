import itertools
import math
from typing import Iterable, Callable, Tuple, Iterator

from GenericSolver import Clue

"""A collection of generators to use in various other puzzles"""
BASE = 10


def allvalues(clue: Clue) -> Iterable[str]:
    """All possible values that fit in the clue length"""
    min_value, max_value = __get_min_max(clue)
    return range(min_value, max_value)


def palindrome(clue: Clue) -> Iterable[str]:
    """Returns palindromes"""
    half_length = (clue.length + 1) // 2
    is_even = (clue.length & 1) == 0
    for i in range(BASE ** (half_length - 1), BASE ** half_length):
        left = str(i)
        right = left[::-1]
        yield left + (right if is_even else right[1:])


def square(clue: Clue) -> Iterable[int]:
    """Returns squares"""
    min_value, max_value = __get_min_max(clue)
    lower = int(math.ceil(math.sqrt(min_value)))
    upper = int(math.ceil(math.sqrt(max_value)))
    return map(lambda x: x * x, range(lower, upper))


def cube(clue: Clue) -> Iterable[int]:
    """Returns cubes"""
    min_value, max_value = __get_min_max(clue)
    lower = int(math.ceil(min_value ** (1 / 3)))
    upper = int(math.ceil(max_value ** (1 / 3)))
    return map(lambda x: x * x * x, range(lower, upper))


def prime(clue: Clue) -> Iterable[int]:
    """Returns primes"""
    return (p for p, is_prime in _prime_not_prime(clue) if is_prime)


def not_prime(clue: Clue) -> Iterable[int]:
    """Returns not primes"""
    return (p for p, is_prime in _prime_not_prime(clue) if not is_prime)


def _prime_not_prime(clue: Clue) -> Iterable[Tuple[int, bool]]:
    """Returns (int, isPrime) for all integers of the right length"""
    min_value, max_value = __get_min_max(clue)
    # Get list of the prime factors that could possibly divide our numbers
    max_factor = int(math.sqrt(max_value))
    factors = list(itertools.takewhile(lambda x: x <= max_factor, __prime()))

    for p in range(min_value, max_value):
        yield p, all(p % factor != 0 for factor in factors)


def known(*values: int) -> Callable[[Clue], Iterable[int]]:
    """Returns a fixed set of already known values"""
    return lambda _: values


def permutation(alphabet: str = '0123456789') -> Callable[[Clue], Iterable[str]]:
    """Returns a non-repeating permutation of digits from the alphabet"""

    def result(clue: Clue) -> Iterable[str]:
        permutations = itertools.permutations(alphabet, clue.length)
        return map(lambda x: ''.join(x), permutations)

    return result


def triangular(clue: Clue) -> Iterable[int]:
    """Returns triangular numbers"""
    return within_clue_limits(clue, (i * (i + 1) // 2 for i in itertools.count(1)))


def fibonacci(clue: Clue) -> Iterable[int]:
    """Returns Fibonacci numbers"""
    return within_clue_limits(clue, __fibonacii_like(1, 2))


def lucas(clue: Clue) -> Iterable[int]:
    """Returns Lucas numbers"""
    return within_clue_limits(clue, __fibonacii_like(2, 1))


def within_clue_limits(clue: Clue, stream: Iterable[int]) -> Iterable[int]:
    """Filters a (possibly infinite) monotonically increasing Iterator so that it only returns those values
    that are within the limits of this clue"""
    min_value, max_value = __get_min_max(clue)
    for value in stream:
        if value >= min_value:
            if value >= max_value:
                return
            yield value


def __get_min_max(clue: Clue) -> Tuple[int, int]:
    min_value = BASE ** (clue.length - 1)
    max_value = BASE * min_value
    return min_value, max_value


def __prime() -> Iterator[int]:
    """The Sieve of Eratosthenes, Python style"""
    numbers = itertools.count(2)
    while True:
        p = next(numbers)
        numbers = filter(lambda x, pp=p: x % pp, numbers)
        yield p


def __fibonacii_like(start_i: int, start_j: int) -> Iterable[int]:
    i, j = start_i, start_j
    while True:
        yield i
        i, j = j, i + j



