import itertools
import re
import typing
from collections import Counter, OrderedDict
from types import CodeType
from typing import Tuple, Callable, Iterable, Union, Optional, Iterator, Dict, cast, Any, NewType, \
    Mapping, FrozenSet, Sequence, List, Set

from DrawGrid import draw_grid

Location = Tuple[int, int]
ClueValueGenerator = Callable[['Clue'], Iterable[Union[str, int]]]
ClueValue = NewType('ClueValue', str)
Letter = NewType('Letter', str)


class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    expression: str
    compiled_expression: CodeType
    generator: Optional[ClueValueGenerator]

    def __init__(self, name: str, is_across: bool, base_location: Location, length: int, *,
                 expression: str = '0',
                 generator: Optional[ClueValueGenerator] = None):
        compiled_expression = self.__get_compiled_expression(expression, name)
        self.name = name
        self.is_across = is_across
        self.base_location = base_location
        self.length = length
        self.expression = expression
        self.compiled_expression = compiled_expression
        self.generator = generator

    def locations(self) -> Iterator[Location]:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        for i in range(self.length):
            yield row + i * row_delta, column + i * column_delta

    def location(self, i: int) -> Location:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        return row + i * row_delta, column + i * column_delta

    def eval(self, known_letters: Dict[Letter, int]) -> Optional[ClueValue]:
        value = eval(self.compiled_expression, None, cast(Any, known_letters))
        if int(value) != value:
            return None
        value = int(value)
        if value < 1:
            return None
        return ClueValue(str(value))

    @staticmethod
    def __get_compiled_expression(expression: str, name: str) -> CodeType:
        expression = expression.replace("–", "-")  # Magpie use a strange minus sign
        expression = expression.replace("^", "**")  # Magpie use a strange minus sign
        for _ in range(2):
            # ), letter, or digit followed by (, letter, or digit needs an * in between, except when we have
            # two digits in a row with no space between them.  Note negative lookahead below.
            expression = re.sub(r'(?!\d\d)([\w)])\s*([(\w])', r'\1*\2', expression)
        if '=' in expression:
            lambda_function = 'lambda x, *y: x if all(z == x for z in y) else -1'
            expression_as_list = expression.replace("=", ",")
            expression = f'({lambda_function})({expression_as_list})'
        return cast(CodeType, compile(expression, f'<Clue {name}>', 'eval'))

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


class ClueList:
    __name_to_clue: Mapping[str, Clue]
    __max_row: int
    __max_column: int
    # The set of all start locations
    __start_locations: FrozenSet[Location]
    # The set of all locations at which two clues intersect
    __intersections: FrozenSet[Location]

    def __init__(self, clues: Sequence[Clue]):
        all_locations: typing.Counter[Location] = Counter(location for clue in clues for location in clue.locations())
        self.__name_to_clue = OrderedDict((clue.name, clue) for clue in clues)
        self.__max_row = 1 + max(row for (row, _) in all_locations)
        self.__max_column = 1 + max(column for (_, column) in all_locations)
        self.__start_locations = frozenset(clue.base_location for clue in clues)
        self.__intersections = frozenset(location for location, count in all_locations.items() if count >= 2)

    @staticmethod
    def create_from_text(across: str, down: str, locations: Sequence[Tuple[int, int]]) -> 'ClueList':
        result: List[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=match.group(2))
                result.append(clue)
        return ClueList(result)

    def get_board(self, clue_values: Dict[Clue, ClueValue]) -> List[List[int]]:
        """Print the board, based on the values for each of the clues"""
        board = [[0 for _ in range(self.__max_column - 1)] for _ in range(self.__max_row - 1)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = int(letter)
        return board

    def print_board(self, clue_values: Dict[Clue, ClueValue]) -> None:
        """Print the board, based on the values for each of the clues"""
        board = [[' ' for _ in range(self.__max_column)] for _ in range(self.__max_row)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))

    def clue_named(self, name: str) -> Clue:
        """Returns the new with the specified name"""
        return self.__name_to_clue[name]

    def __iter__(self) -> Iterator[Clue]:
        return iter(self.__name_to_clue.values())

    def is_intersection(self, location: Location) -> bool:
        return location in self.__intersections

    def is_start_location(self, location: Location) -> bool:
        return location in self.__start_locations

    def verify_is_vertically_symmetric(self) -> None:
        """Verify that the puzzle has vertical symmetry"""
        clue_start_set = self.__make_clue_start_set()
        for clue in self:
            # The location in this clue that matches the start of its mirror opposite
            row, column = clue.location(clue.length - 1 if clue.is_across else 0)
            # The presumed start location of its mirror opposite
            row2, column2 = row, self.__max_column - column
            assert ((row2, column2), clue.length, clue.is_across) in clue_start_set

    def verify_is_180_symmetric(self) -> None:
        """Verify that the puzzle has 180° symmetry"""
        clue_start_set = self.__make_clue_start_set()
        for clue in self:
            # The location in this clue that matches the start of its symmetric opposite
            row, column = clue.location(clue.length - 1)
            # The presumed start location of its symmetric opposite
            row2, column2 = self.__max_row - row, self.__max_column - column
            if ((row2, column2), clue.length, clue.is_across) not in clue_start_set:
                raise Exception(f"No opposite for {clue.name} @ {clue.base_location}")

    def verify_is_four_fold_symmetric(self) -> None:
        """Verify that the puzzle has four-fold symmetry"""
        # for each clue, we make sure the next one clockwise is also there.
        assert self.__max_row == self.__max_column
        clue_start_set = self.__make_clue_start_set()
        for clue in self:
            # The location in this clue that matches the start of its 90° clockwise rotation
            row, column = clue.location(0 if clue.is_across else clue.length - 1)
            # The presumed start location of the clue located 90° clockwise.
            row2, column2 = column, self.__max_column - row
            # Note that across clues rotate to down clues, and vice versa.
            assert ((row2, column2), clue.length, not clue.is_across) in clue_start_set

    def __make_clue_start_set(self) -> Set[Tuple[Location, int, bool]]:
        """Creates the set of (start-location, length, is-across) tuples for all clues in the puzzle"""
        return {(clue.base_location, clue.length, clue.is_across) for clue in self.__name_to_clue.values()}

    def plot_board(self, clue_values: Dict[Clue, ClueValue]) -> None:
        max_row = self.__max_row
        max_column = self.__max_column

        # Locations that are part of some clue, whether we know the answer or not.
        clued_locations: Set[Location] = set()

        # A map from location to value to put in that location.
        location_to_entry: Dict[Location, str] = {}

        # A map from location to clue number to put in that location
        location_to_clue_number: Dict[Location, str] = {}

        # Location of squares that have a heavy bar on their left.
        left_bars = set(itertools.product(range(1, max_row), range(2, max_column)))

        # Location of squares that have a heavy bar at their top
        top_bars = set(itertools.product(range(2, max_row), range(1, max_column)))

        # Note that we determine top_bars and left_bars by elimination.  We originally place all
        # possible locations in the set, then remove those bars that are in the interior of a clue.
        # The location of left heavy bars, top heavy bars, and squares that are part of an answer

        for clue in self:
            match = re.search(r'\d+', clue.name)
            if match:
                location_to_clue_number[clue.base_location] = match.group(0)
            else:
                old = location_to_clue_number.get(clue.base_location)
                location_to_clue_number[clue.base_location] = f'{old}, {clue.name}' if old else clue.name

            # These squares are filled.
            clued_locations.update(clue.locations())
            if clue in clue_values:
                for location, value in zip(clue.locations(), clue_values[clue]):
                    location_to_entry[location] = value
            # These are internal locations of an answer, so a heavy bar isn't needed.
            (left_bars if clue.is_across else top_bars).difference_update(
                (clue.location(i) for i in range(1, clue.length)))

        draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                  top_bars, left_bars)
