import functools
import functools
import itertools
import math
import operator
from collections import Counter
from fractions import Fraction
from typing import Tuple, Sequence, Any, Iterable

from misc.primes import PRIMES, PRIMES_LIMIT

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
    prime_set = set(PRIMES)

    # 44680   362800
    def is_prime(value: int) -> bool:
        if value <= PRIMES_LIMIT:
            return value in prime_set
        return is_prime_large(value)

    @functools.lru_cache(None)
    def is_prime_large(value: int) -> bool:
        sqrt = math.isqrt(value)
        for prime in PRIMES:
            if prime > sqrt:
                return True
            if value % prime == 0:
                return False

    def get_partitions(n: int, smallest: int, permutation_pairs, foo=()):
        print(9-n, foo, len(permutation_pairs))
        if n == 0:
            return len(permutation_pairs)
        count = 0
        for i in range(smallest, n + 1):
            if i == n:
                variables = [int(permutation[-n:]) for _, permutation in permutation_pairs]
            else:
                if n - i < i: continue
                variables = [int(permutation[-n: -n + i]) for _, permutation in permutation_pairs]
            prime_variables = {x for x in set(variables) if is_prime(x)}
            next = [(variable, permutation)
                    for variable, (prev, permutation) in zip(variables, permutation_pairs)
                    if variable > prev and variable in prime_variables]
            if next:
                count += get_partitions(n - i, i, next, foo + (i,))
        return count


    def run2():
        permutations = [(0, ''.join(x)) for x in itertools.permutations("123456789")]
        return get_partitions(9, 1, permutations)

    return run2()


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


def foobar():
    prime_set = set(PRIMES)

    # 44680   362800
    def is_prime(value: int) -> bool:
        if value <= PRIMES_LIMIT:
            return value in prime_set
        return is_prime_large(value)

    @functools.lru_cache(None)
    def is_prime_large(value: int) -> bool:
        sqrt = math.isqrt(value)
        for prime in PRIMES:
            if prime > sqrt:
                return True
            if value % prime == 0:
                return False

    @functools.lru_cache(None)
    def get_order_of_prime(n):
        factors = prime_factors(n - 1)
        result = n
        for prime, count in factors:
            result = result // (prime ** count)
            a = pow(10, result, n)
            while a != 1:
                a = pow(a, prime, n); result = result * prime
        return result

    def get_repl_n(value):
        assert value % 2 != 0 and value % 5 != 0
        factors = prime_factors(value * 9)
        result = 1
        for prime, count in factors:
            assert prime != 2
            if prime == 3:
                assert count >= 2
                this_result = prime ** (count - 2)
            elif prime == 483:
                this_result = prime - 1 if count <= 2 else (prime - 1) * prime ** (count - 2)
            else:
                this_result = get_order_of_prime(prime) * prime ** (count - 1)
            result = result * this_result // math.gcd(result, this_result)
        return result

    maximum = 100_000
    total = 0
    for prime in PRIMES:
        if prime > maximum:
            break
        elif prime == 2 or prime == 5:
            total += prime
        else:
            value = temp = get_repl_n(prime)
            while temp % 2 == 0: temp //= 2
            while temp % 5 == 0: temp //= 5
            if temp == 1:
                print(prime, value)
            else:
                total += prime
    return total

def foobar():
    from sympy.parsing.sympy_parser import parse_expr
    from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application
    transformations = (standard_transformations + (implicit_multiplication_application,))
    print(parse_expr("xy", transformations=transformations))


if __name__ == '__main__':
    foobar()







