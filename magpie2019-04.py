import collections
import itertools
import re
from typing import Optional, Tuple, Dict, List, Iterator, NewType, NamedTuple, Sequence, Any, Callable, Iterable, \
    Pattern, Set, FrozenSet

Location = Tuple[int, int]
ClueValue = NewType('ClueValue', str)


LOCATION_TO_CLUE_DICT: Dict[Location, List[Tuple['Clue', int]]] = collections.defaultdict(list)


class Clue(NamedTuple):
    name: str
    base_location: Location
    length: int
    is_across: bool
    generator: Callable[[int], Iterable[int]]
    sparseness: int

    def locations(self) -> Iterator[Location]:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        for i in range(self.length):
            yield row + i * row_delta, column + i * column_delta

    def location(self, i: int) -> Location:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        return row + i * row_delta, column + i * column_delta
    
    def generate(self, base: int) -> Iterator[ClueValue]:
        min_value = base ** (self.length - 1)
        max_value = min_value * base
        for i in self.generator(base):
            if i >= min_value:
                if i >= max_value:
                    return
                yield ClueValue(Clue.to_base(i, base))

    @staticmethod
    def to_base(num: int, base: int) -> str:
        result = []
        if not num:
            return '0'
        while num:
            num, mod = divmod(num, base)
            result.append(str(mod))
        result.reverse()
        return ''.join(result)

    @staticmethod
    def verify_is_180_symmetric() -> None:
        max_row = 1 + max(row for (row, _) in LOCATION_TO_CLUE_DICT.keys())
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        for clue in CLUES:
            row, column = clue.base_location
            # Find the item(s) in the diagonally opposite location of the same type
            others = {(x, y) for (x, y) in LOCATION_TO_CLUE_DICT[(max_row - row, max_column - column)]
                      if x.is_across == clue.is_across}
            # There better be exactly one, and it better have the same length, and its index must be appropriate
            assert len(others) == 1
            clue2, index2 = others.pop()
            assert clue2.length == clue.length
            assert index2 == clue.length - 1
        # While we're at it, make sure the numbers are consistent.
        for clue1, clue2 in itertools.permutations(CLUES, 2):
            if clue1.name[1:] == clue2.name[1:]:
                # Same numbers but one is across and the other is down.
                assert clue1.base_location == clue2.base_location

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


def make(name: str, base_location: Location, length: int, generator: Callable[[int], Iterable[int]]) -> 'Clue':
    if generator == cube:
        sparseness = 10
    elif generator in (square, triangular, lucas, fibonacci):
        sparseness = 9
    elif generator == palindrome:
        sparseness = 7
    else:
        sparseness = 6
    result = Clue(name, base_location, length, name[0] == 'A', generator, sparseness)
    for i, location in enumerate(result.locations()):
        LOCATION_TO_CLUE_DICT[location].append((result, i))
    return result


def triangular(_: int) -> Iterator[int]:
    for i in itertools.count(1):
        yield i * (i + 1) // 2


def square(_: int) -> Iterator[int]:
    for i in itertools.count(1):
        yield i * i


def cube(_: int) -> Iterator[int]:
    for i in itertools.count(1):
        yield i * i * i


def fibonacci(_: int) -> Iterator[int]:
    i, j = 1, 2
    while True:
        yield i
        i, j = j, i + j


def lucas(_: int) -> Iterator[int]:
    i, j = 2, 1
    while True:
        yield i
        i, j = j, i + j


def palindrome(base: int) -> Iterator[int]:
    for i in range(1, base):
        for j in range(0, base):
            yield i * base * base + j * base + i


def prime(_: int) -> Iterable[int]:
    return 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97


CLUES = (
    make('A1', (1, 1), 3, triangular),
    make('A3', (1, 4), 2, triangular),
    make('A4', (2, 1), 2, lucas),
    make('A5', (2, 3), 3, triangular),
    make('A8', (3, 2), 3, fibonacci),
    make('A10', (4, 1), 3, triangular),
    make('A12', (4, 4), 2, triangular),
    make('A14', (5, 1), 2, lucas),
    make('A15', (5, 3), 3, square),

    make('D1', (1, 1), 2, prime),
    make('D2', (1, 2), 3, palindrome),
    make('D3', (1, 4), 2, cube),
    make('D5', (2, 3), 3, fibonacci),
    make('D6', (2, 5), 2, lucas),
    make('D7', (3, 1), 2, square),
    make('D9', (3, 4), 3, square),
    make('D11', (4, 2), 2, cube),
    make('D13', (4, 5), 2, fibonacci)
)


class Intersection(NamedTuple):
    this_index: int
    other_clue: Clue
    other_index: int

    @staticmethod
    def maybe_make(this: Clue, other: Clue) -> Optional['Intersection']:
        if this.is_across == other.is_across:
            return None
        this_row, this_column = this.base_location
        other_row, other_column = other.base_location
        row_delta, column_delta = other_row - this_row, other_column - this_column
        # if "this" is an across clue, the clash is at (this_row, other_column).
        # if "this" is a down clue, the class is at (this_column, other_row).
        my_index, other_index = (column_delta, -row_delta) if this.is_across else (row_delta, -column_delta)
        if 0 <= my_index < this.length and 0 <= other_index < other.length:
            return Intersection(my_index, other, other_index)
        return None

    def values_match(self, this_value: ClueValue, known_clues: Dict[Clue, ClueValue]) -> bool:
        return this_value[self.this_index] == known_clues[self.other_clue][self.other_index]

    @staticmethod
    def get_pattern_maker(clue: Clue, intersections: Sequence['Intersection']) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        temp = ['.'] * (clue.length + 1)
        temp[-1] = '$'
        if not intersections:
            # This is just an optimization.  getter() would work just fine.
            pattern = re.compile(''.join(temp))
            return lambda x: pattern
        else:
            def getter(known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
                result = temp[:]
                for intersection in intersections:
                    result[intersection.this_index] = known_clues[intersection.other_clue][intersection.other_index]
                return re.compile(''.join(result))
            return getter


DEBUG = True


class SolvingStep(NamedTuple):
    clue: Clue
    pattern_maker: Callable[[Dict[Clue, ClueValue]], Pattern[str]]


class Solver:
    count_total: int
    known_clues: Dict[Clue, ClueValue]
    base: int
    solving_steps: Sequence[SolvingStep]

    def __init__(self) -> None:
        self.solving_steps = Solver._get_solving_steps()

    @staticmethod
    def _get_solving_steps() -> Sequence[SolvingStep]:
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Clue, Tuple[Clue, List[Intersection]]] = {
            clue: (clue, [])
            for clue in CLUES
        }

        def evaluator(item: Tuple[Clue, List[Intersection]]) -> Sequence[Any]:
            clue, intersections = item
            return clue.sparseness, len(intersections), len(intersections) - clue.length

        while not_yet_ordered:
            clue, intersections = max(not_yet_ordered.values(), key=evaluator)
            not_yet_ordered.pop(clue)
            result.append(SolvingStep(clue, Intersection.get_pattern_maker(clue, intersections)))
            for (other_clue, other_filled_crossing_clues) in not_yet_ordered.values():
                maybe_clash = Intersection.maybe_make(other_clue, clue)
                if maybe_clash:
                    other_filled_crossing_clues.append(maybe_clash)
        return tuple(result)

    def solve(self, base: int) -> None:
        self.base = base
        self.count_total = 0
        self.known_clues = {}
        self.__solve(0)

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_steps):
            self._print_board()
            return
        solving_step = self.solving_steps[current_index]
        clue = solving_step.clue
        pattern = solving_step.pattern_maker(self.known_clues)
        try:
            for value in clue.generate(self.base):
                self.count_total += 1

                def show_it(info: str) -> None:
                    if DEBUG:
                        print(f'{" | " * current_index} {clue.name} {value} ({clue.length}): {info}')

                if value in self.known_clues.values():
                    continue

                if not pattern.match(value):
                    continue

                self.known_clues[clue] = value
                show_it('--->')
                self.__solve(current_index + 1)
        finally:
            self.known_clues.pop(clue, None)

    def _print_board(self) -> None:
        max_row = 1 + max(row for (row, _) in LOCATION_TO_CLUE_DICT.keys())
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        board = [[' ' for _ in range(max_column)] for _ in range(max_row)]
        for clue, clue_value in self.known_clues.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))

class Solver2:
    count_total: int
    known_clues: Dict[Clue, ClueValue]
    base: int

    def __init__(self) -> None:
        pass

    def solve(self, base: int) -> None:
        self.base = base
        self.count_total = 0
        self.known_clues = {}
        start_list = {clue: frozenset(clue.generate(base)) for clue in CLUES }
        self.__solve(start_list)

    def __solve(self, current_list: Dict[Clue, FrozenSet[ClueValue]]) -> None:
        depth = len(self.known_clues)
        if not current_list:
            self._print_board()
            return
        clue, values = min(current_list.items(), key=lambda x: len(x[1]))
        if not values:
            if DEBUG or True:
                print(f'{" | " * depth}{clue.name} XX')
            return
        try:
            for i, value in enumerate(sorted(values)):
                def update(clue2: Clue, values2: FrozenSet[ClueValue]) -> FrozenSet[ClueValue]:
                    intersection = Intersection.maybe_make(clue2, clue)
                    if intersection:
                        my_index = intersection.this_index
                        needed_char = value[intersection.other_index]
                        result = frozenset(x for x in values2 if x != value and x[my_index] == needed_char)
                    else:
                        result = values2 - { value }
                    if DEBUG and result != values2:
                        print(f'{"   " * depth}   {clue2.name} {list(sorted(values2))} -> {list(sorted(result))}')
                    return result
                if DEBUG or True:
                    print(f'{" | " * depth}{clue.name} {i + 1}/{len(values)}: {value} -->')
                self.known_clues[clue] = value
                next_list = { clue2 : update(clue2, values2)
                              for (clue2, values2) in current_list.items() if clue2 != clue}
                self.__solve(next_list)
        finally:
            self.known_clues.pop(clue, None)


    def _print_board(self) -> None:
        max_row = 1 + max(row for (row, _) in LOCATION_TO_CLUE_DICT.keys())
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        board = [[' ' for _ in range(max_column)] for _ in range(max_row)]
        for clue, clue_value in self.known_clues.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))


def run() -> None:
    Clue.verify_is_180_symmetric()
    solver = Solver2()
    solver.solve(9)


def foo():
    for x in (10, 15, 21):
        for y in (67, 78, 89):
            t = x + y
            if 80 <= t <= 99: print(x, y, t)

if __name__ == '__main__':
    foo()
    # run()
