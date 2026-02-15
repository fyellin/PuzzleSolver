import itertools
from collections import defaultdict, Counter
from typing import Dict, Tuple, List, Sequence, Iterator, Callable, FrozenSet

from solver import Clues, ConstraintSolver, Clue, generators, ClueValue, KnownClueDict


def is_harshad(value: int) -> bool:
    """
    Check if an integer is a Harshad (Niven) number in base 10.
    
    Returns:
        `true` if the integer is divisible by the sum of its decimal digits, `false` otherwise.
    """
    digits = map(int, list(str(value)))
    return value % sum(digits) == 0


def create_harshard_table() -> Dict[Tuple[str, str], List[int]]:
    table: Dict[Tuple[str, str], List[int]] = defaultdict(list)
    for value in (x for x in range(100, 1000) if is_harshad(x)):
        temp = str(value)
        key = (temp[0], temp[2])
        table[key].append(value)
    return table


def create_solving_table() -> Iterator[Tuple[int, int, List[List[int]]]]:
    count = 0
    table = create_harshard_table()
    for start in range(100, 500):
        for delta in range(100, 200):
            a, b, c, d, e, f = [str(start + delta * i) for i in range(0, 6)]
            if len(f) >= 4:
                break
            if a[0] != f[2] or c[2] != d[0]:
                continue
            # if str(delta % 10) != e[1]:
            #     continue
            temp1 = f[0:2] + a + b
            temp2 = c[0:2] + d + e
            if all(table[v1, v2] for v1, v2 in zip(temp1, temp2)):
                yield start, delta, [table[v1, v2] for v1, v2 in zip(temp1, temp2)]
                count += 1
    print(f"Total of {count} rows")


GRID = """
X..XX.
.XXX.X
..X...
X..X..
"""


class Solver207(ConstraintSolver):
    start_to_harshards: Dict[Tuple[int, int], List[List[int]]]
    start_to_harshard_set: Dict[Tuple[int, int], FrozenSet[int]]

    @staticmethod
    def run() -> None:
        solver = Solver207()
        solver.solve(debug=True)

    def __init__(self) -> None:
        self.start_to_harshards = {}
        self.start_to_harshard_set = {}
        for start, delta, harshards in create_solving_table():
            self.start_to_harshards[start, delta] = harshards
            self.start_to_harshard_set[start, delta] = frozenset(x for harshard in harshards for x in harshard)

        super().__init__(self.make_clue_list())

        self.add_constraint(('1a', '4d'), self.delta_constraint)
        self.add_constraint(('1a', '4d', '2a'), self.sequence_element_constraint(1))
        self.add_constraint(('1a', '4d', '7d'), self.sequence_element_constraint(2))
        self.add_constraint(('1a', '4d', '10a'), self.sequence_element_constraint(3))
        self.add_constraint(('1a', '4d', '9a'), self.sequence_element_constraint(4))
        self.add_constraint(('1a', '4d', '1d'), self.sequence_element_constraint(5))

        self.add_constraint(('1a', '4d', '5d', '6d'), self.handle_5d_6d)

    def make_clue_list(self) -> Sequence[Clue]:
        def square_or_triangular(clue: Clue) -> Iterator[int]:
            yield from generators.square(clue)
            yield from generators.triangular(clue)

        locations = Clues.get_locations_from_grid(GRID)
        clues = [
            Clue('1a', True, locations[0], 3,
                 generator=generators.known(*[start for (start, _) in self.start_to_harshards.keys()])),
            Clue('2a', True, locations[1], 3, generator=generators.allvalues),
            Clue('4a', True, locations[3], 3, generator=square_or_triangular),
            Clue('8a', True, locations[7], 3, generator=square_or_triangular),
            Clue('9a', True, locations[8], 3, generator=generators.allvalues),
            Clue('10a', True, locations[9], 3, generator=generators.allvalues),
            Clue('1d', False, locations[0], 3, generator=generators.allvalues),
            Clue('3d', False, locations[2], 3, generator=generators.triangular),
            Clue('4d', False, locations[3], 3,
                 generator=generators.known(*[delta for (_, delta) in self.start_to_harshards.keys()])),
            Clue('5d', False, locations[4], 2, generator=generators.allvalues),
            Clue('6d', False, locations[5], 2, generator=generators.allvalues),
            Clue('7d', False, locations[6], 3, generator=generators.allvalues),
        ]
        return clues

    @staticmethod
    def sequence_element_constraint(item_number: int) -> Callable[[ClueValue, ClueValue, ClueValue], bool]:
        def checker(a1: ClueValue, d4: ClueValue, my_value: ClueValue) -> bool:
            expected_value = str(int(a1) + item_number * int(d4))
            if item_number >= 3:
                expected_value = expected_value[::-1]
            return my_value == expected_value

        return checker

    def delta_constraint(self, a1: ClueValue, d4: ClueValue) -> bool:
        return (int(a1), int(d4)) in self.start_to_harshards

    def handle_5d_6d(self, a1: ClueValue, d4: ClueValue, d5: ClueValue, d6: ClueValue) -> bool:
        product = int(d5) * int(d6)
        return product in self.start_to_harshard_set[int(a1), int(d4)]

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        a1 = int(known_clues[self.clue_named('1a')])
        d4 = int(known_clues[self.clue_named('4d')])
        d5 = int(known_clues[self.clue_named('5d')])
        d6 = int(known_clues[self.clue_named('6d')])
        product = d5 * d6
        locations = {location: letter
                     for clue in self._clue_list
                     for location, letter in zip(clue.locations, known_clues[clue])}
        middle_eight = Counter(locations[x, y] for x in (2, 3) for y in (2, 3, 4, 5))

        for harshads in itertools.product(*self.start_to_harshards[a1, d4]):
            if product not in harshads:
                continue
            harshads_eight = Counter(str(x)[1] for x in harshads)
            if harshads_eight == middle_eight:
                print(harshads)
                return True
        return False


if __name__ == '__main__':
    # (954, 114, 126, 330, 621, 207, 915, 156)
    Solver207.run()