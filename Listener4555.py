import itertools
import math
from typing import Callable, Iterable, Optional, Dict, List, FrozenSet, Union, Sequence, Mapping
import functools

import Generators
from GenericSolver import ClueValueGenerator, Clue, Location, ClueValue, ClueList, SolverByClue

"""
Looking at 16a/17d, the only number/cube that intersect that way are:
      17d = 11, 6a=1331

If I’m reading the instructions correctly, each line is broken up into multiple primes; primes don’t cross lines.  
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

primes = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107,
          109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229,
          233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359,
          367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491,
          499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641,
          643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787,
          797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941,
          947, 953, 967, 971, 977, 983, 991, 997, 1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051, 1061, 1063,
          1069, 1087, 1091, 1093, 1097, 1103, 1109, 1117, 1123, 1129, 1151, 1153, 1163, 1171, 1181, 1187, 1193, 1201,
          1213, 1217, 1223, 1229, 1231, 1237, 1249, 1259, 1277, 1279, 1283, 1289, 1291, 1297, 1301, 1303, 1307, 1319,
          1321, 1327, 1361, 1367, 1373, 1381, 1399, 1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453, 1459, 1471,
          1481, 1483, 1487, 1489, 1493, 1499, 1511, 1523, 1531, 1543, 1549, 1553, 1559, 1567, 1571, 1579, 1583, 1597,
          1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657, 1663, 1667, 1669, 1693, 1697, 1699, 1709, 1721, 1723,
          1733, 1741, 1747, 1753, 1759, 1777, 1783, 1787, 1789, 1801, 1811, 1823, 1831, 1847, 1861, 1867, 1871, 1873,
          1877, 1879, 1889, 1901, 1907, 1913, 1931, 1933, 1949, 1951, 1973, 1979, 1987, 1993, 1997, 1999, 2003, 2011,
          2017, 2027, 2029, 2039, 2053, 2063, 2069, 2081, 2083, 2087, 2089, 2099, 2111, 2113, 2129, 2131, 2137, 2141,
          2143, 2153, 2161, 2179, 2203, 2207, 2213, 2221, 2237, 2239, 2243, 2251, 2267, 2269, 2273, 2281, 2287, 2293,
          2297, 2309, 2311, 2333, 2339, 2341, 2347, 2351, 2357, 2371, 2377, 2381, 2383, 2389, 2393, 2399, 2411, 2417,
          2423, 2437, 2441, 2447, 2459, 2467, 2473, 2477, 2503, 2521, 2531, 2539, 2543, 2549, 2551, 2557, 2579, 2591,
          2593, 2609, 2617, 2621, 2633, 2647, 2657, 2659, 2663, 2671, 2677, 2683, 2687, 2689, 2693, 2699, 2707, 2711,
          2713, 2719, 2729, 2731, 2741, 2749, 2753, 2767, 2777, 2789, 2791, 2797, 2801, 2803, 2819, 2833, 2837, 2843,
          2851, 2857, 2861, 2879, 2887, 2897, 2903, 2909, 2917, 2927, 2939, 2953, 2957, 2963, 2969, 2971, 2999, 3001,
          3011, 3019, 3023, 3037, 3041, 3049, 3061, 3067, 3079, 3083, 3089, 3109, 3119, 3121, 3137, 3163, 3167, 3169,
          3181, 3187, 3191, 3203, 3209, 3217, 3221, 3229, 3251, 3253, 3257, 3259, 3271, 3299, 3301, 3307, 3313, 3319,
          3323, 3329, 3331, 3343, 3347, 3359, 3361, 3371, 3373, 3389, 3391, 3407, 3413, 3433, 3449, 3457, 3461, 3463,
          3467, 3469, 3491, 3499, 3511, 3517, 3527, 3529, 3533, 3539, 3541, 3547, 3557, 3559, 3571, 3581, 3583, 3593,
          3607, 3613, 3617, 3623, 3631, 3637, 3643, 3659, 3671, 3673, 3677, 3691, 3697, 3701, 3709, 3719, 3727, 3733,
          3739, 3761, 3767, 3769, 3779, 3793, 3797, 3803, 3821, 3823, 3833, 3847, 3851, 3853, 3863, 3877, 3881, 3889,
          3907, 3911, 3917, 3919, 3923, 3929, 3931, 3943, 3947, 3967, 3989)

prime_set = set(primes)

prime_string_set = set(str(x) for x in primes if 2 < x < 1662)


@functools.lru_cache(maxsize=None)
def break_row_into_primes(line: str) -> List[List[str]]:
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
    return Generators.within_clue_limits(clue, (i * i - 1 for i in itertools.count(1)))


def generate_18a(_clue: Clue) -> Iterable[int]:
    """We just make sure it is a value that can be parsed into primes.  We check that it is the sum later"""
    return (i for i in range(100, 1000) if break_row_into_primes(f'1331{i}'[0:6]))


def generate_1d(_clue: Clue) -> Iterable[int]:
    # We know that it ends in 11.
    return range(1_000_011, 10_000_000, 100)


def generate_2d(_clue: Clue) -> Iterable[int]:
    # We know that last two digits are 37, and other five digits are all 1,3,5,7
    for temp in itertools.product((1, 3, 7, 9), repeat=5):
        value = sum(x * (10 ** i) for i, x in enumerate(temp)) * 100 + 37
        if value % 21 == 0 and all(value % x == 0 for x in temp):
            yield value


def generate_3d(_clue: Clue) -> Iterable[int]:
    # Not currently used
    # We know that it ends with 37, and is a non-prime
    return (i for i in range(1_000_037, 10_000_000, 100) if any(i % prime == 0 for prime in primes))


def generate_6d(_clue: Clue) -> Iterable[int]:
    # We know that it is a multiple of 9, and it ends in a 6.  We start with the smallest multiple of 9, and skip by 90.
    return range(1_000_026, 10_000_000, 90)


def with_prime_pattern(function: Callable[[Clue], Iterable[Union[int, str]]]) -> Callable[[Clue], Iterable[str]]:
    return lambda clue: (x for x in map(str, function(clue)) if break_row_into_primes(x))


def make(name: str, base_location: Location, length: int, generator: Optional[ClueValueGenerator]) -> Clue:
    return Clue.make(name, name[0] == 'A', base_location, length, generator=generator)


CLUES = (
    make('A1',  (1, 1), 7, with_prime_pattern(Generators.cube)),
    make('A8',  (2, 1), 3, Generators.not_prime),
    make('A9',  (2, 4), 4, Generators.known(1173, 1927, 2777)),
    make('A10', (3, 1), 7, with_prime_pattern(Generators.permutation())),
    make('A12', (4, 1), 2, Generators.prime),
    make('A13', (4, 3), 3, generate_13a),
    make('A14', (4, 6), 2, Generators.not_prime),
    make('A15', (5, 1), 7, with_prime_pattern(Generators.permutation())),
    make('A16', (6, 1), 4, Generators.known(1331)),
    make('A18', (6, 5), 3, generate_18a),
    make('A19', (7, 1), 7, with_prime_pattern(Generators.known(1771569))),

    make('D1',  (1, 1), 7, generate_1d),  # additional constraints added by A12
    make('D2',  (1, 2), 7, generate_2d),
    make('D3',  (1, 3), 7, None),  # this is checked in show_solutions()
    make('D4',  (1, 4), 2, Generators.not_prime),
    make('D5',  (1, 5), 7, Generators.square),
    make('D6',  (1, 6), 7, generate_6d),
    make('D7',  (1, 7), 7, Generators.known(1173**2, 1927**2, 2777**2)),
    make('D11', (3, 4), 3, Generators.palindrome),
    make('D17', (6, 4), 2, Generators.known(11)),
)


class MySolver(SolverByClue):
    def __init__(self, clue_list: ClueList):
        super(MySolver, self).__init__(clue_list)
        self.a8 = clue_list.clue_named("A8")
        self.a9 = clue_list.clue_named("A9")
        self.a12 = clue_list.clue_named("A12")
        self.a13 = clue_list.clue_named("A13")
        self.a14 = clue_list.clue_named("A14")
        self.a18 = clue_list.clue_named("A18")
        self.d1 = clue_list.clue_named('D1')
        self.d3 = clue_list.clue_named("D3")
        self.d7 = clue_list.clue_named("D7")

    def get_allowed_regexp(self, location: Location) -> str:
        _, column = location
        if column == 2:
            # As explained in the intro, the second column can only contain these digits
            return '[1379]'
        else:
            return super(MySolver, self).get_allowed_regexp(location)

    def post_clue_assignment_fixup(self, clue: Clue, known_clues: Mapping[Clue, ClueValue],
                                   unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
        result = True
        if clue.name == 'A12':
            # D1 must be a multiple of A12
            value = int(known_clues[clue])
            unknown_clues[self.d1] = frozenset(x for x in unknown_clues[self.d1] if int(x) % value == 0)
            result = bool(unknown_clues[self.d1])
        elif clue.name == 'A9' or clue.name == 'D7':
            result = self.check_clue_filter(self.a9, self.d7, known_clues, unknown_clues, lambda a9, d7: d7 == a9 * a9)
        if not result:
            return False

        if clue.name in ('A8', 'A9'):
            return self.__force_row_to_be_series_of_primes(known_clues, unknown_clues, (self.a8, self.a9))
        elif clue.name in ('A12', 'A13', 'A14'):
            return self.__force_row_to_be_series_of_primes(known_clues, unknown_clues, (self.a12, self.a13, self.a14))
        else:
            return True

    @staticmethod
    def __force_row_to_be_series_of_primes(known_clues: Mapping[Clue, ClueValue],
                                           unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                           clues: Sequence[Clue], ) -> bool:
        """
        If all but one of the clues indicated has a known value, restrict its values to be only those that
        satisfy that you can break the completed row into primes.
        """
        not_yet_assigned_clues = [clue for clue in clues if clue not in known_clues]
        if len(not_yet_assigned_clues) == 1:
            not_yet_assigned_clue = not_yet_assigned_clues[0]
            # Create a format string consisting of the known line patterns, but put {} where the unknown goes
            line_pattern = ''.join(known_clues.get(clue, '{}') for clue in clues)
            new_set = unknown_clues[not_yet_assigned_clue] = frozenset(
                # Filter out those results that don't create a proper line pattern
                result for result in unknown_clues[not_yet_assigned_clue]
                if break_row_into_primes(line_pattern.format(result)))
            return bool(new_set)
        return True

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        board = self.clue_list.get_board(known_clues)

        # A18 must be the sum of the digits in the grid
        answer_a18 = int(known_clues[self.a18])
        total = sum(board[i][j] for i in range(7) for j in range(7))
        if total != answer_a18:
            return

        # D3 must not be prime
        answer_d3 = sum(board[i][2] * 10 ** (6 - i) for i in range(7))
        if all(answer_d3 % prime != 0 for prime in primes):
            return

        rows = [''.join(str(board[row][column]) for column in range(7)) for row in range(7)]
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
            self.clue_list.print_board(known_clues)


def run() -> None:
    clue_list = ClueList.create(CLUES)
    clue_list.verify_is_180_symmetric()
    solver = MySolver(clue_list)
    solver.solve(debug=False)


# ((59, 29, 7, 41), (89, 3, 11, 73), (19, 43, 587), (61, 67, 53, 5), (47, 83, 659), (13, 31, 23), (17, 71, 569))
if __name__ == '__main__':
    run()
