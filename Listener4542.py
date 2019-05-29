import collections
import re
from types import CodeType
from typing import Optional, Tuple, Dict, List, Iterator, NewType, NamedTuple, Sequence, Any, Callable, Iterable, \
    Pattern, Set

import inflect  # type: ignore

eng = inflect.engine()

Location = Tuple[int, int]
ClueValue = NewType('ClueValue', str)


LOCATION_TO_CLUE_DICT: Dict[Location, List[Tuple['Clue', int]]] = collections.defaultdict(list)


def create_length_to_integer_dict() -> Tuple[Dict[Tuple[int, int], List[ClueValue]], Dict[ClueValue, ClueValue]]:
    result: Dict[Tuple[int, int], List[ClueValue]] = collections.defaultdict(list)
    word_sums = dict()
    for i in range(1, 1000):
        clue_value = ClueValue(str(i))
        word = ''.join(i for i in eng.number_to_words(i) if i.islower())
        length = len(str(i))
        word_length = len(word)
        word_sums[clue_value] = ClueValue(str(sum(ord(c) - ord('a') + 1 for c in set(word))))
        result[(length, word_length)].append(clue_value)
    return result, word_sums


LENGTHS_TO_INTEGERS, WORD_SUMS = create_length_to_integer_dict()


class Clue(NamedTuple):
    name: str
    base_location: Location
    length: int
    num_letters: int
    expression: str
    compiled_expression: CodeType
    expression_letters: Set[str]
    is_across: bool

    def locations(self) -> Iterator[Location]:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        for i in range(self.length):
            yield row + i * row_delta, column + i * column_delta

    def location(self, i: int) -> Location:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        return row + i * row_delta, column + i * column_delta

    def eval(self, dictionary: Dict[str, int]) -> Optional[ClueValue]:
        value = eval(self.compiled_expression, None, dictionary)
        if int(value) != value:
            return None
        value = int(value)
        if value < 1:
            return None
        return ClueValue(str(value))

    def generate(self) -> Iterable[ClueValue]:
        # Find all locations that are the start of a clue: this one or another
        starts = {index for index, location in enumerate(self.locations())
                  for (_, other_index) in LOCATION_TO_CLUE_DICT[location]
                  if other_index == 0}
        # Don't allow a zero in any of those locations
        for value in LENGTHS_TO_INTEGERS[(self.length, self.num_letters)]:
            if all(value[x] != '0' for x in starts):
                yield value

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

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name} at {self.base_location}/{self.length}>'

    def __repr__(self) -> str:
        return str(self)


def make(name: str, expression: str, num_letters: int, length: int, base_location: Location) -> 'Clue':
    expression_to_compile = expression
    if '=' in expression:
        lambda_function = 'lambda x, *y: x if all(z == x for z in y) else -1'
        expression_as_list = expression_to_compile.replace("=", ",")
        expression_to_compile = f'({lambda_function})({expression_as_list})'
    compiled_expression = compile(expression_to_compile, '<string>', 'eval')
    expression_letters = set(ch for ch in expression if ch.isalpha())
    result = Clue(name, base_location, length, num_letters, expression,
                  compiled_expression, expression_letters, name.isupper())

    for i, location in enumerate(result.locations()):
        LOCATION_TO_CLUE_DICT[location].append((result, i))
    return result


CLUES = (
    #     definition        num_letters len x  y
    make('A', 'n',                  6, 2, (1, 1)),
    make('B', 'e',                 16, 3, (1, 3)),
    make('C', 'f + k/A = k + d/A', 23, 3, (2, 1)),
    make('D', 'M - H',             21, 3, (2, 4)),
    make('E', 'f',                 23, 3, (3, 2)),
    make('F', 'k - b',             11, 2, (3, 5)),
    make('G', 'd',                  9, 2, (4, 1)),
    make('H', 'E',                 24, 3, (4, 3)),
    make('K', 'B - b = d + G',     25, 3, (5, 1)),
    make('M', 'G',                 18, 3, (5, 4)),
    make('N', 'B',                 23, 3, (6, 2)),
    make('P', 'c',                 10, 2, (6, 5)),
    make('a', 'C',                 23, 3, (1, 2)),
    make('b', 'A + G',              9, 2, (1, 3)),
    make('c', 'E',                 22, 3, (1, 5)),
    make('d', 'F',                 11, 2, (1, 6)),
    make('e', '(h -  F) / 2',      23, 3, (2, 1)),
    make('f', 'H',                 25, 3, (2, 4)),
    make('g', '(H +  D) / 2',      23, 3, (3, 3)),
    make('h', 'G',                 11, 3, (3, 6)),
    make('k', 'H',                 24, 3, (4, 2)),
    make('m', 'C - b',             22, 3, (4, 5)),
    make('n', 'G',                 10, 2, (5, 1)),
    make('p', 'D',                  9, 2, (5, 4)),
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


class Solver2:
    count_total: int
    known_clues: Dict[Clue, ClueValue]
    base: int

    def __init__(self) -> None:
        pass

    def solve(self) -> None:
        self.count_total = 0
        self.known_clues = {}
        possible_values = {clue: list(clue.generate()) for clue in CLUES}
        self.__solve(possible_values)

    def __solve(self, possible_values: Dict[Clue, List[ClueValue]]) -> None:
        depth = len(self.known_clues)
        if not possible_values:
            self._print_board()
            return
        clue, values = min(possible_values.items(), key=lambda x: len(x[1]))
        if not values:
            if DEBUG or True:
                print(f'{"|  " * depth}{clue.name} 0/0')
            return
        try:
            known_letters = {x.name for x in self.known_clues}
            known_letters.add(clue.name)
            new_expressions = {x for x in CLUES
                               if x.expression_letters.issubset(known_letters) and clue.name in x.expression_letters}
            if new_expressions:
                print(f'{"|  " * depth}{clue.name} CLUES: {[x.name for x in new_expressions]}')

            for i, value in enumerate(values):
                self.count_total += 1
                print(f'{"|  " * depth}{clue.name} {i + 1}/{len(values)}: {value} -->')
                self.known_clues[clue] = value

                next_possible_values = possible_values.copy()
                if new_expressions:
                    dictionary = {clue.name: int(value) for clue, value in self.known_clues.items()}

                    def handle_expression(expression: Clue) -> bool:
                        evaluation = expression.eval(dictionary)
                        if expression.name in known_letters:
                            answer = self.known_clues[expression]
                            word_sums = WORD_SUMS[answer]
                            result = (word_sums == evaluation)
                            print(f'{"|  " * depth}*{expression.name} wc({answer}) = {word_sums} '
                                  f'{"=" if result else "!="} {evaluation}')
                            return result
                        else:
                            old_npv = next_possible_values[expression]
                            new_npv = [t for t in next_possible_values[expression] if WORD_SUMS[t] == evaluation]
                            print(f'{"|  " * depth}*{expression.name} {old_npv} -> {new_npv}')
                            next_possible_values[expression] = new_npv
                            return bool(new_npv)

                    if not all(handle_expression(x) for x in new_expressions):
                        continue

                def update(this_clue: Clue, this_value: List[ClueValue]) -> List[ClueValue]:
                    intersection = Intersection.maybe_make(this_clue, clue)
                    if intersection:
                        my_index = intersection.this_index
                        needed_char = value[intersection.other_index]
                        result = [x for x in this_value if x != value and x[my_index] == needed_char]
                    else:
                        result = [x for x in this_value if x != value]
                    return result

                next_possible_values.pop(clue)
                for clue2, value2 in next_possible_values.items():
                    next_possible_values[clue2] = update(clue2, value2)
                    if value2 != next_possible_values[clue2]:
                        print(f'{"|  " * depth}+{clue2.name} {value2} -> {next_possible_values[clue2]}')

                self.__solve(next_possible_values)

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
    solver.solve()
    print(solver.count_total)


if __name__ == '__main__':
    run()
