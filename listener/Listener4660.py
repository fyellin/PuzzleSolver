import itertools
import math
from collections.abc import Callable, Iterator, Sequence

from more_itertools import sieve

from solver import (
    AbstractClueValue,
    Clue,
    Clues,
    ConstraintSolver,
    KnownClueDict,
    generators,
)
from solver.helpers import digit_sum, is_square, is_triangular

PRIMES_2DIGIT = {x for x in sieve(100) if x > 10}
PRIMES_2DIGIT_STR = {str(x) for x in PRIMES_2DIGIT}


class MyString(AbstractClueValue):
    """Grid entry text is ``str(entry)``; subtype of ``AbstractClueValue``."""

    __slots__ = ('value', 'entry', 'prime', 'offset')

    def __init__(self, value: int, entry: int, prime: int, offset: int) -> None:
        self.value = value
        self.entry = entry
        self.prime = prime
        self.offset = offset
        super().__init__(str(entry))

    @staticmethod
    def get(value: int | str) -> list[MyString]:
        temp = str(value)
        return [MyString(value=int(value), prime=int(prime), entry=int(rest), offset=i)
                for i in range(0, len(temp) - 1)
                for prime in [temp[i:i + 2]] if prime in PRIMES_2DIGIT_STR
                for rest in [temp[0:i] + temp[i + 2:]] if rest[0] != '0']

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, MyString)
                and (self.value, self.offset) == (other.value, other.offset))

    def __hash__(self) -> int:
        return hash((self.value, self.offset))

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, MyString):
            return NotImplemented
        return (self.value, self.offset) < (other.value, other.offset)

    def __repr__(self) -> str:
        temp = str(self.value)
        o = self.offset
        return f'{temp[0:o]}/{temp[o:o + 2]}/{temp[o + 2:]}'


def generate_palindrome(clue: Clue) -> Iterator[MyString]:
    length = clue.length + 2
    """Returns palindromes"""
    half_length = (length + 1) // 2
    is_even = (length & 1) == 0
    for i in range(10 ** (half_length - 1), 10 ** half_length):
        left = str(i)
        right = left[::-1]
        value = int(left + (right if is_even else right[1:]))
        yield from MyString.get(value)


def generate_special_squares(clue: Clue) -> Iterator[MyString]:
    # Squares in which the removed prime number's reverse is also prime
    min_value, max_value = 10 ** (clue.length + 1), 10 ** (clue.length + 2)
    lower = math.ceil(math.sqrt(min_value))
    upper = math.ceil(math.sqrt(max_value))

    def has_backwards_prime(x: MyString) -> bool:
        return str(x.prime)[::-1] in PRIMES_2DIGIT_STR

    return filter(has_backwards_prime,
                  (x for i in range(lower, upper) for x in MyString.get(i * i)))


def generate_15_across(_clue: Clue) -> Iterator[MyString]:
    for i in range(100):
        cube = i * i * i
        if 10000 <= cube <= 99999:
            for temp in MyString.get(cube):
                v = math.isqrt(temp.entry)
                if v in PRIMES_2DIGIT and v * v == temp.entry:
                    yield temp


def generate_ascending(clue: Clue) -> Iterator[MyString]:
    length = clue.length + 2
    for digits in itertools.combinations("123456789", length):
        yield from MyString.get(''.join(digits))


def generate_descending(clue: Clue) -> Iterator[MyString]:
    length = clue.length + 2
    for digits in itertools.combinations("9876543210", length):
        yield from MyString.get(''.join(digits))


def generate_triangle(clue: Clue) -> Iterator[MyString]:
    fake_clue = Clue("fake", True, (1, 1), clue.length + 2)
    for value in generators.triangular(fake_clue):
        yield from MyString.get(value)


def generate_prime(clue: Clue) -> Iterator[MyString]:
    fake_clue = Clue("fake", True, (1, 1), clue.length + 2)
    for value in generators.prime(fake_clue):
        yield from MyString.get(value)


def generate_all(clue: Clue) -> Iterator[MyString]:
    fake_clue = Clue("fake", True, (1, 1), clue.length + 2)
    for value in generators.allvalues(fake_clue):
        yield from MyString.get(value)


def generate_if(generator, test: Callable[[MyString], bool]):
    def result(clue: Clue):
        return [x for x in generator(clue) if test(x)]

    return result


GRID = """
XXXXXX
XX.XX.
X.X.X.
.X.X.X
X.X...
"""

ACROSSES = [
    (2, 3, generate_if(generate_all, lambda x: x.value % x.entry == 0)),
    (5, 2, generate_special_squares),
    (7, 3, generate_if(generate_all, lambda x: x.value % x.prime == 0 and x.entry % x.prime == 0)),
    (9, 2, generate_all),
    (11, 2, generate_ascending),
    (12, 2, generate_if(generate_triangle, lambda x: is_triangular(x.entry))),
    (13, 2, generate_prime),
    (14, 2, generate_triangle),
    (15, 3, generate_15_across),
    (17, 2, generate_special_squares),
    (18, 3, generate_if(generate_all, lambda x: x.prime // 10 < x.prime % 10))
]

DOWNS = [
    (1, 2, generate_if(generate_all, lambda p: p.value % p.prime == 0)),
    (3, 2, generate_special_squares),
    (4, 3, generate_all),
    (6, 3, generate_palindrome),
    (8, 3, generate_descending),
    (10, 3, generate_if(generate_ascending, lambda x: x.value % digit_sum(x.value) == 0)),
    (11, 3, generate_ascending),
    (12, 3, generate_all),
    (15, 2, generate_special_squares),
    (16, 2, generate_if(generate_all, lambda x: x.value % x.prime == 0))
]


class Solver6220(ConstraintSolver):
    @staticmethod
    def run():
        solver = Solver6220()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)
        self.add_all_constraints()
        self.seen = False

    @staticmethod
    def get_clues() -> Sequence[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            letter = 'a' if is_across else 'd'
            for number, length, generator in information:
                clue = Clue(f'{number}{letter}', is_across, grid[number - 1], length,
                            generator=generator)
                clues.append(clue)
        return clues

    def add_all_constraints(self) -> None:
        self.add_constraint(("5a", "17a"), lambda a, b: str(a.prime) == str(b.prime)[::-1])
        self.add_constraint(("3d", "15d"), lambda a, b: str(a.prime) == str(b.prime)[::-1])
        self.add_constraint(("17a", "3d"), lambda a, b: str(a.entry) == str(b.entry)[::-1])
        self.add_constraint(("9a", "4d"), lambda a, b: a.value % b.prime == 0)
        self.add_constraint(("11a", "11d"),
                            lambda a, b: b.entry % a.entry == 0 and a.prime + b.prime == b.entry)
        self.add_constraint(("18a", "11d"), lambda a, b: a.entry % b.prime == 0)
        self.add_constraint(("18a", "12a"), lambda a, b: a.value % b.prime == 0)

        self.add_constraint(("15a", "7a"), lambda a, b: a.value == b.prime ** 3)
        self.add_constraint(("15a", "6d"), lambda a, b: a.entry == b.prime ** 2)

        self.add_constraint(("1d", "16d"), lambda a, b: is_triangular(a.prime + b.prime))
        self.add_constraint(("4d", "2a"), lambda a, b: a.value % b.prime == 0)
        self.add_constraint(("6d", "14a", "8d"), lambda a, b, c: a.entry == b.prime * c.prime)
        self.add_constraint(("12d", "18a"),
                            lambda a, b: sorted(str(a.entry)) == sorted(str(b.entry)) and
                                         digit_sum(a.value) == digit_sum(b.value))
        self.add_constraint(("16d", "1d"), lambda a, b: is_square(a.entry + b.entry))

        two_digit_entries = {x for x in self.clue_list if x.length == 2}
        others = list(two_digit_entries - {self.clue_named("9a")})

        def handle_9a(a9, *other_clues):
            value = int(str(a9.entry)[::-1])
            return any(x.entry == value for x in other_clues)

        self.add_constraint(("9a", *others), handle_9a)

        for a, b in itertools.combinations(self.clue_list, 2):
            self.add_constraint(
                (a, b),
                lambda x, y: x.prime != y.prime and x.entry != y.entry and x.value != y.value)

    def show_solution(self, known_clues: KnownClueDict) -> None:
        if not self.seen:
            print(' '.join(f'{clue.name:<8}' for clue in self.clue_list))
            self.seen = True
        print(' '.join(f'{known_clues[clue].__repr__():<8}' for clue in self.clue_list))
        # super().show_solution(known_clues)


if __name__ == '__main__':
    Solver6220.run()
