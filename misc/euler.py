import functools
import datetime
import itertools
import math
from collections import defaultdict, Counter, deque
from fractions import Fraction
from typing import Tuple, Sequence, Any, Set, Iterable
import numpy as np
import fraction

import operator

num2words = {1: 'One', 2: 'Two', 3: 'Three', 4: 'Four', 5: 'Five',
             6: 'Six', 7: 'Seven', 8: 'Eight', 9: 'Nine', 10: 'Ten',
            11: 'Eleven', 12: 'Twelve', 13: 'Thirteen', 14: 'Fourteen',
            15: 'Fifteen', 16: 'Sixteen', 17: 'Seventeen', 18: 'Eighteen',
            19: 'Nineteen', 20: 'Twenty', 30: 'Thirty', 40: 'Forty',
            50: 'Fifty', 60: 'Sixty', 70: 'Seventy', 80: 'Eighty',
            90: 'Ninety', 0: 'Zero'}

@functools.lru_cache(None)
def number_to_word(x):
    if x in num2words:
        return num2words[x]
    elif x < 100:
        tens, units = divmod(x, 10)
        return num2words[tens * 10] + num2words[units]
    elif x < 1000:
        hundreds, remainder = divmod(x, 100)
        temp = num2words[hundreds] + "Hundred"
        if remainder > 0:
            temp += "And" + number_to_word(remainder)
        return temp
    else:
        thousands, remainder = divmod(x, 1000)
        temp = number_to_word(thousands) + "Thousand"
        if remainder > 0:
            temp += number_to_word(remainder)
        return temp


CARD_VALUES = { '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10,
                'J': 11, 'Q': 12, 'K': 13, 'A': 14}

def get_poker_value(cards: Sequence[str]) -> Tuple[int, Sequence[Tuple[int, int]]]:
    is_flush = len({card[1] for card in cards}) == 1
    values = Counter(CARD_VALUES[card[0]] for card in cards)
    sorted_cards = sorted(((count, value) for value, count in values.items()), reverse=True)
    is_straight = len(sorted_cards) == 5 and sorted_cards[0][1] == sorted_cards[-1][1] + 4
    if is_flush and is_straight:
        return (100, sorted_cards)
    elif len(sorted_cards) == 2:
        # 4 of a kind or a full house
        return (80, sorted_cards)
    elif is_flush:
        return (60, sorted_cards)
    elif is_straight:
        return (40, sorted_cards)
    else:
        return (25 - len(sorted_cards), sorted_cards)

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

def divisor_count(value: int):
    factorization = prime_factors(value)
    return functools.reduce(operator.mul, (count + 1 for _prime, count in factorization), 1)

def product(values):
    return functools.reduce(operator.mul, values, 1)

def phi(value: int):
    current = value
    for prime, _ in  prime_factors(value):
        current = (current // prime) * (prime - 1)
    return current

@functools.lru_cache(None)
def sum_factors(value: int):
    factorization = prime_factors(value)
    try:
        xtra = [(prime ** (count + 1) - 1) // (prime - 1) for prime, count in factorization]
        return functools.reduce(operator.mul, xtra, 1) - value
    except:
        print("huh")

def digit_sum(value: int) -> int:
    return sum(int(x) for x in str(value))

def continued_fraction_sqrt(n: int) -> Iterable[int]:
    cache = {}
    sqrt_n = math.sqrt(n)
    a = Fraction(1)
    b = Fraction(0)
    while True:
        if (a, b) in cache:
            digit, a, b = cache[a, b]
        else:
            old_a, old_b = a, b
            digit = int(math.floor(a * sqrt_n + b))
            b = b - digit
            denominator = a * a * n - b * b
            a, b = a / denominator, -b / denominator
            cache[old_a, old_b] = digit, a, b
        yield digit

def convergents(fraction) -> Iterable[Tuple[int, int]]:
    n, d = next(fraction), 1
    yield n, d

    digit = next(fraction)
    n, prev_n = digit * n + 1, n
    d, prev_d = digit, d
    yield n, d

    for digit in fraction:
        n, prev_n = digit * n + prev_n, n
        d, prev_d = digit * d + prev_d, d
        yield n, d


@functools.lru_cache(None)
def partition(n):
    if n == 0:
        return 1
    if n < 0:
        return 0
    sum = 0
    for k in itertools.count(1):
        t1 = k * (3 * k - 1) // 2
        t2 = k * (3 * k + 1) // 2
        assert t2 == t1 + k
        multiplier = 1 if (k % 2 == 1) else -1
        if t1 <= n:
            sum += multiplier * partition(n - t1)
        if t2 <= n:
            sum += multiplier * partition(n - t2)
        if t2 >= n:
            return sum % 1_000_000

def read_url(url):
    import urllib.request
    fp = urllib.request.urlopen(url)
    mybytes = fp.read()
    return mybytes.decode("utf")


def is_special_set(values):
    values = sorted(values)
    if any(x == y for x, y in zip(values[1:], values[:1])):
        return False

    for i in range(1, (len(values) + 1) // 2):
        if sum(values[:i+1]) <= sum(values[-i:]):
            return False

    for length in range(1, (len(values)) + 1):
        all_sums = [sum(x) for x in itertools.combinations(values, length)]
        if len(set(all_sums)) != len(all_sums):
            return False

    return True


def foobar() -> Any:
    # 166 is wrong answer
    def is_palindrome(number):
        temp = str(number)
        return temp == temp[::-1]

    maximum = 10 ** 8

    indices = np.arange(0, math.isqrt(maximum // 2) + 10)
    squares = indices ** 2
    squares_cumsum = np.cumsum(squares)
    matrix = squares_cumsum[:, None] - squares_cumsum[None, :]
    matrix[(indices[:, None] < indices[None, :] + 2)]  = 0

    items = { int(value) for value in np.nditer(matrix) if 0 < value < maximum and is_palindrome(value)}
    print(len(items), sorted(items), sum(items))







if __name__ == '__main__':
    print(foobar())
