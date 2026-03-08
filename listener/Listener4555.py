"""
Painful, but relatively straightforward.
"""

import functools
import itertools
from collections.abc import Callable, Iterable, Sequence

from more_itertools import is_prime, sieve

from solver import (
    Clue,
    ClueValueGenerator,
    ConstraintSolver,
    KnownClueDict,
    Location,
    generators,
)

"""
Looking at 16a/17d, the only number/cube that intersect that way are:
      17d = 11, 6a=1331

If I'm reading the instructions correctly, each line is broken up into multiple primes;
primes don't cross lines.
That severely restricts 7d.  Every digit has to be the last digit of a different prime.
Hence there must be at most a single 2, and the rest of the digits must be odd.  Also, it must be a perfect square (9a)
and its second digit must be the same as the last digit of its square root.  Hunting gives us:
  9a    7d
1173 1375929
1927 3713329
2777 7711729

So no matter what 19a ends in 9.  That means it has to the sum of even and odd.  So the first factor is 2**3, and we 
hunt for the second power that gives us a 7-digit number ending in 9.  The possible results are:
     19a                    
  5764809 = 8 +  7 **  8   
  1771569 = 8 + 11 **  6   
  1874169 = 8 + 37 **  4   
  2825769 = 8 + 41 **  4   
  3418809 = 8 + 43 **  4   
  4879689 = 8 + 47 **  4   
  7890489 = 8 + 53 **  4   

Since 17d=11, the fourth digit of 19a is 1, and the only possible answer is the second one above.  
Nicely, its fifth digit is a 5, which is a legitimate way to end a square.

Since 2d ends in a 7, and yet is a multiple of all of its digits, none of the digits can be 0,2,4,5,6,8.  The only
possible digits for it are 1,3,7,or 9.

"""

primes = list(sieve(4000))

prime_string_set = {str(x) for x in sieve(1662)}


@functools.cache
def break_row_into_primes(line: str) -> list[list[str]]:
    result = []
    length = len(line)
    for i in range(1, 5):
        if i < length:
            if line[i] == '0':
                continue
            line_prefix = line[0:i]
            if line_prefix in prime_string_set:
                for value in break_row_into_primes(line[i:]):
                    if line_prefix not in value:
                        result.append([line_prefix] + value)
        else:
            if line in prime_string_set:
                result.append([line])
            break

    return result


def generate_13a(clue: Clue) -> Iterable[int]:
    return generators.within_clue_limits(clue, (i * i - 1 for i in itertools.count(1)))


def generate_18a(_clue: Clue) -> Iterable[int]:
    """We just make sure it is a value that can be parsed into primes.  We check that it is the sum later"""
    return (i for i in range(100, 1000) if break_row_into_primes(f'1331{i}'[0:6]))


def generate_1d(_clue: Clue) -> Iterable[int]:
    # We know that it ends in 11.
    return range(1_000_011, 10_000_000, 100)


def generate_2d(_clue: Clue) -> Iterable[int]:
    # We know that the last two digits are 37, and other five digits are all 1,3,5,7
    for temp in itertools.product((1, 3, 7, 9), repeat=5):
        value = sum(x * (10 ** i) for i, x in enumerate(temp)) * 100 + 37
        if value % 21 == 0 and all(value % x == 0 for x in temp):
            yield value


def generate_3d(_clue: Clue) -> Iterable[int]:
    # Not currently used
    # We know that it ends with 37 and that it is a non-prime
    return itertools.filterfalse(is_prime, range(1_000_037, 10_000_000, 100))


def generate_6d(_clue: Clue) -> Iterable[int]:
    # We know that it is a multiple of 9, and it ends in a 6.
    # We start with the smallest multiple of 9 and skip by 90.
    return range(1_000_026, 10_000_000, 90)


def with_prime_pattern(function: Callable[[Clue], Iterable[int | str]]) -> Callable[[Clue], Iterable[str]]:
    return lambda clue: (x for x in map(str, function(clue)) if break_row_into_primes(x))


def make(name: str, base_location: Location, length: int, generator: ClueValueGenerator | None) -> Clue:
    return Clue(name, name[0] == 'A', base_location, length, generator=generator)


CLUES = (
    make('A1', (1, 1), 7, with_prime_pattern(generators.cube)),
    make('A8', (2, 1), 3, generators.not_prime),
    make('A9', (2, 4), 4, generators.known(1173, 1927, 2777)),
    make('A10', (3, 1), 7, with_prime_pattern(generators.permutation())),
    make('A12', (4, 1), 2, generators.prime),
    make('A13', (4, 3), 3, generate_13a),
    make('A14', (4, 6), 2, generators.not_prime),
    make('A15', (5, 1), 7, with_prime_pattern(generators.permutation())),
    make('A16', (6, 1), 4, generators.known(1331)),
    make('A18', (6, 5), 3, generate_18a),
    make('A19', (7, 1), 7, with_prime_pattern(generators.known(1771569))),

    make('D1',  (1, 1), 7, generate_1d),  # additional constraints added by A12
    make('D2',  (1, 2), 7, generate_2d),
    make('D3',  (1, 3), 7, None),  # this is checked in show_solutions()
    make('D4', (1, 4), 2, generators.not_prime),
    make('D5', (1, 5), 7, generators.square),
    make('D6',  (1, 6), 7, generate_6d),
    make('D7', (1, 7), 7, generators.known(1173 ** 2, 1927 ** 2, 2777 ** 2)),
    make('D11', (3, 4), 3, generators.palindrome),
    make('D17', (6, 4), 2, generators.known(11)),
)


class MySolver(ConstraintSolver):
    def __init__(self, clue_list: Sequence[Clue]):
        super().__init__(clue_list)
        self.add_constraint(('A12', 'D1'), lambda a12, d1: int(d1) % int(a12) == 0)
        self.add_constraint(('A9', 'D7'), lambda a9, d7: int(d7) == int(a9) ** 2)
        self.add_constraint(('A8', 'A9'), lambda a8, a9: bool(break_row_into_primes(a8 + a9)))
        self.add_constraint(('A12', 'A13', 'A14'), lambda a12, a13, a14: bool(break_row_into_primes(a12 + a13 + a14)))

    def get_allowed_regexp(self, location: Location) -> str:
        _, column = location
        if column == 2:
            # As explained in the intro, the second column can only contain these digits
            return '[1379]'
        else:
            return super().get_allowed_regexp(location)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        # A map from locations to the value in that location.
        board = self.get_board(known_clues)

        # A18 must be the sum of the digits in the grid
        answer_a18 = int(known_clues[self.clue_named("A18")])
        total = sum(int(board[i, j]) for i in range(1, 8) for j in range(1, 8))
        if total != answer_a18:
            return False

        # D3 must not be prime
        d3 = self.clue_named("D3")
        answer_d3 = int(''.join([board[location] for location in d3.locations]))
        if is_prime(answer_d3):
            return False

        rows = [''.join(str(board[row, column]) for column in range(1, 8)) for row in range(1, 8)]
        rows[5] = rows[5][0:-1]
        row_breaks = tuple(break_row_into_primes(row) for row in rows)
        for row_break in itertools.product(*row_breaks):
            values = [x for xx in row_break for x in xx]
            values.append('2')  # Put back the two that we removed from rows[5]
            if not len(values) == len(set(values)) == 25:
                continue
            if sum(map(int, values)) != 2662:  # 2 * A16
                continue
            print(row_break)
            return True
        return False


def run() -> None:
    solver = MySolver(CLUES)
    solver.verify_is_180_symmetric()
    solver.solve()


# ((59, 29, 7, 41), (89, 3, 11, 73), (19, 43, 587), (61, 67, 53, 5), (47, 83, 659), (13, 31, 23), (17, 71, 569))
if __name__ == '__main__':
    run()
