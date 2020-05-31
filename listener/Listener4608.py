import itertools
import math
from typing import Sequence, Optional, Iterator, Set, Callable, Dict, Any

from solver import Clue, generators, ClueValue
from solver import ConstraintSolver
from solver import Location
from solver.constraint_solver import KnownClueDict
from solver.generators import ClueValueGenerator


def generate_L(clue: Clue) -> Iterator[int]:
    """Prime.  Digit sume is fibonacci.  Length 3"""
    for prime in generators.prime(clue):
        if digit_sum(prime) in {1, 2, 3, 5, 8, 13, 21, 34, 55}:
            yield prime


def generate_T(clue: Clue) -> Iterator[int]:
    """Divisible by digit sum"""
    for number in generators.allvalues(clue):
        if number % digit_sum(number) == 0:
            yield number


def generate_a(clue: Clue) -> Iterator[int]:
    """Contains a zero"""
    for number in generators.allvalues(clue):
        if '0' in str(number):
            yield number


def generate_k(clue: Clue) -> Iterator[int]:
    """prime with repeated digit"""
    for prime in generators.prime(clue):
        temp = str(prime)
        if len(temp) != len(set(temp)):
            yield prime


def generate_l(clue: Clue) -> Iterator[int]:
    "1000 less than a triangular number"
    triangulars = (i * (i + 1) // 2 for i in itertools.count(1))
    min_value, max_value = generators.get_min_max(clue)
    min_value += 1000
    max_value += 1000
    for value in triangulars:
        if value >= min_value:
            if value >= max_value:
                return
            yield value - 1000


def generate_q(clue: Clue) -> Iterator[str]:
    """Digits in increasing order"""
    for digits in itertools.combinations("123456789", clue.length):
        yield ''.join(digits)


def generate_r(clue: Clue) -> Iterator[str]:
    """Digits in decreasing order"""
    for digits in itertools.combinations("9876543210", clue.length):
        yield ''.join(digits)


def make(name: str, length: int, base_location: Location, *, generator: Optional[ClueValueGenerator] = None) -> 'Clue':
    return Clue(name, name.isupper(), base_location, length, generator=generator or generators.allvalues)


CLUES = (
    #     definition        num_letters len x  y
    make('A', 3, (1, 3)),
    make('B', 3, (1, 7)),
    make('C', 5, (2, 4), generator=generators.palindrome),
    make('D', 3, (3, 5), generator=generators.palindrome),
    make('E', 3, (4, 1)),
    make('F', 2, (4, 4)),
    make('G', 2, (4, 7), generator=generators.not_prime),
    make('H', 3, (4, 9)),
    make('J', 3, (5, 2)),
    make('K', 3, (5, 5)),
    make('L', 3, (5, 8), generator=generate_L),
    make('M', 2, (6, 1)),
    make('N', 2, (6, 3), generator=generators.prime),
    make('P', 3, (6, 5)),
    make('Q', 2, (6, 8), generator=generators.triangular),
    make('R', 2, (6, 10)),
    make('S', 2, (7, 2), generator=generators.prime),
    make('T', 2, (7, 4), generator=generate_T),
    make('U', 2, (7, 7), generator=generators.palindrome),
    make('V', 2, (7, 9)),
    make('W', 2, (8, 4)),
    make('X', 2, (8, 7), generator=generators.palindrome),

    make('a', 3, (1, 3), generator=generate_a),
    make('b', 2, (1, 4), generator=generators.not_prime),
    make('c', 3, (1, 5)),
    make('d', 5, (1, 6)),
    make('e', 3, (1, 7), generator=generators.not_prime),
    make('f', 2, (1, 8), generator=generators.triangular),
    make('g', 3, (1, 9)),

    make('h', 3, (3, 4), generator=generators.palindrome),
    make('i', 3, (3, 8)),
    make('j', 2, (4, 1)),
    make('k', 3, (4, 3), generator=generate_k),
    make('l', 3, (4, 5), generator=generate_l),
    make('m', 3, (4, 7)),
    make('n', 3, (4, 9)),
    make('*', 2, (4, 11)),

    make('ß', 2, (5, 2)),
    make('o', 2, (5, 10)),
    make('p', 3, (6, 1)),
    make('q', 3, (6, 4), generator=generate_q),
    make('r', 3, (6, 6), generator=generate_r),
    make('s', 3, (6, 8)),
    make('t', 3, (6, 11)),
    make('u', 2, (7, 2)),
    make('v', 2, (7, 3), generator=generators.square),
    make('w', 2, (7, 5), generator=generators.nth_power(4)),
    make('x', 2, (7, 7), generator=generators.square),
    make('y', 2, (7, 9), generator=generators.not_prime),
    make('z', 2, (7, 10)),
)


def digit_sum(x: int) -> int:
    return sum(int(digit) for digit in str(x))


def digit_product(x: int) -> int:
    return math.prod(int(digit) for digit in str(x))


def is_factor(x: int, y: int) -> bool:
    return x < y and y % x == 0


def is_cube(number: int) -> bool:
    number = abs(number)  # Prevents errors due to negative numbers
    return round(number ** (1 / 3)) ** 3 == number


def is_anagram(x: int, y: int) -> bool:
    return sorted(str(x)) == sorted(str(y))


def generator_fibonacci_to(limit: int) -> Set[int]:
    def generator() -> Iterator[int]:
        i, j = 0, 1
        while True:
            yield i
            i, j = j, i + j
    return set(itertools.takewhile(lambda x: x < limit, generator()))


FIBONACCIS = generator_fibonacci_to(10000)


class Listener4608(ConstraintSolver):
    def __init__(self, clue_list: Sequence[Clue]) -> None:
        super(Listener4608, self).__init__(clue_list)

        self.my_constraint(("A", "n", "K"), lambda A, n, K: A == n - K)
        self.my_constraint(("B", "o"), lambda B, o: B == o * digit_sum(o) + 1)
        self.my_constraint(("E", "Q", "u", "B"), lambda E, Q, u, B: E == Q * u - 5 * B)
        self.my_constraint(("F", "u"), lambda F, u: F == u + 1)
        self.my_constraint(("G", "g"), lambda G, g: is_factor(G, digit_product(g)))
        self.my_constraint(("J", "v"), lambda J, v: is_cube(J - v))
        self.my_constraint(("K", "n"), lambda K, n: is_anagram(K, n))
        self.my_constraint(("M", 'f'), lambda M, f: M == 2 * f)
        self.my_constraint(("N", "Q"), lambda N, Q: digit_sum(N) == digit_sum(Q))
        self.my_constraint(("P", "q", "y"), lambda P, q, y: P == q + y)
        self.my_constraint(("R", "V"), lambda R, V: is_factor(R, V))
        self.my_constraint("VC", lambda V, C: V == digit_product(V) + digit_sum(C))
        self.my_constraint("WXT", lambda W, X, T: W == X - T)

        self.my_constraint("cx", lambda c, x: is_factor(x, c))
        self.my_constraint("dQna", lambda d, Q, n, a: d == 2 * Q * n + a)
        self.my_constraint("fC", lambda f, C: is_factor(f, C))
        self.my_constraint("in", lambda i, n: (i - n) in FIBONACCIS)
        self.my_constraint("jA", lambda j, A: digit_product(j) == digit_product(A))
        self.my_constraint("ma", lambda m, a: is_factor(a, m))
        self.my_constraint("nx", lambda n, x: is_factor(x, n))
        self.my_constraint("or", lambda o, r: o == digit_product(r))
        self.my_constraint("prt", lambda p, r, t: 2 * t == p + r)
        self.my_constraint("sS", lambda s, S: s == 9 * S)
        self.my_constraint("tQvV", lambda t, Q, v, V: t == Q * v + V)
        self.my_constraint("u*", lambda u, star: u > star)
        self.my_constraint("vH", lambda v, H: is_factor(v, H))
        self.my_constraint("zc", lambda z, c: is_factor(digit_product(c), z))

    def my_constraint(self, variables: Sequence[str], predicate: Callable[..., bool]) -> None:
        def new_predicate(*values: str) -> bool:
            return predicate(*(int(x) for x in values))
        self.add_constraint(variables, new_predicate)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        """
        H Twice the sum of the 76 digits in the grid (3)
        g One more than another entry (3)
       """
        clue_g = self.clue_named("g")
        g_minus_1 = str(int(known_clues[clue_g])- 1)
        if not g_minus_1 in known_clues.values():
            return False

        clue_H = self.clue_named("H")
        locations_to_entries = {location: int(digit)
                                for clue, value in known_clues.items()
                                for location, digit in zip(clue.locations, value)}
        assert len(locations_to_entries) == 76
        digit_sum = str(2 * sum(locations_to_entries.values()))
        if digit_sum != known_clues[clue_H]:
            return False

        return True

    def show_solution(self, known_clues: KnownClueDict) -> None:
        super().show_solution(known_clues)
        clues_and_values = sorted((clue.name, value) for clue, value in known_clues.items())
        clues_and_values.sort()
        all_clues, all_values = zip(*clues_and_values)
        print(f'({", ".join(all_clues)}) = ({", ".join(all_values)})')
        locations_to_entries = {location: digit
                                for clue, value in known_clues.items()
                                for location, digit in zip(clue.locations, value)}
        message = ''.join(locations_to_entries[location] for location in sorted(locations_to_entries.keys()))
        self.handle_message(message, int(known_clues[self.clue_named('*')]))

    @staticmethod
    def handle_message(message: str, divisor: int) -> None:
        assert len(message) == 76
        print(f'Message = "{message}"')
        print(f'Digit sum is {sum(int(x) for x in message)}')
        pieces = [int(message[i:i+2]) for i in range(0, len(message), 2)]
        print(pieces)
        pieces = [x % divisor for x in pieces]
        print(pieces)
        letters = [chr(ord('A') + digit - 1) for digit in pieces]
        print(''.join(letters))

    def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                  location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
                  top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:
        location_to_clue_number[5, 2] = 'J'

        shaded_squares = {location for location, value in location_to_entry.items() if value in "13579"}
        shading = {location: "lightgreen" for location in shaded_squares}

        super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number, top_bars,
                          left_bars, shading=shading, **more_args)

def run() -> None:
    solver = Listener4608(CLUES)
    solver.verify_is_vertically_symmetric()
    solver.solve(debug=True, max_debug_depth=5)

    return

    clues = "ABCDEFGHJKLMNPQRSTUVWXabcdefghijklmnopqrstuvwxyzß*"
    values = (162, 649, 54045, 595, 495, 69, 54, 752, 359, 573, 337, 90, 73, 395, 55, 29, 61, 48, 44, 58, 51, 99, 107,
              65, 245, 80957, 645, 45, 943, 969, 743, 43, 557, 953, 535, 735, 72, 934, 345, 942, 549, 938, 68, 16, 81,
              49, 50, 80, 30, 25)
    known_clues = { solver.clue_named(letter): ClueValue(str(value)) for (letter, value) in zip(clues, values)}
    solver.show_solution(known_clues)



if __name__ == '__main__':
    run()

