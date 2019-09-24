import itertools
import re
import typing
from collections import Counter, OrderedDict
from typing import Mapping, FrozenSet, Sequence, Tuple, List, Dict, Iterator, Set, Any

from .clue import Clue
from .clue_types import Location, ClueValue
from .draw_grid import draw_grid


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
    def get_locations_from_grid(grid: str) -> Sequence[Location]:
        grid = grid.strip()
        return [(row + 1, column + 1)
                for row, line in enumerate(grid.splitlines())
                for column, item in enumerate(line)
                if item == 'X']

    @classmethod
    def create_from_text(cls, across: str, down: str, locations: Sequence[Tuple[int, int]]) -> 'ClueList':
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
        return cls(result)

    def get_board(self, clue_values: Dict[Clue, ClueValue]) -> List[List[str]]:
        """Print the board, based on the values for each of the clues"""
        board = [['' for _ in range(self.__max_column)] for _ in range(self.__max_row)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row][column] = letter
        return board

    def clue_named(self, name: str) -> Clue:
        """Returns the new with the specified name"""
        return self.__name_to_clue[name]

    def __iter__(self) -> Iterator[Clue]:
        return iter(self.__name_to_clue.values())

    def is_intersection(self, location: Location) -> bool:
        return location in self.__intersections

    def is_start_location(self, location: Location) -> bool:
        return location in self.__start_locations

    # Override this if there are addition restrictions on the value that can go into a field.
    def get_allowed_regexp(self, location: Location) -> str:
        return '.' if self.is_zero_allowed(location) else '[^0]'

    # Only used by get_allowed_regexp.  The normal rule is that zeros are allowed everywhere except at beginning
    def is_zero_allowed(self, location: Location) -> bool:
        """Returns true if a 0 is allowed at this clue location.  Overrideable by subclasses"""
        return not self.is_start_location(location)

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

    def plot_board(self, clue_values: Dict[Clue, ClueValue], **more_args: Any) -> None:
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
                    if location in location_to_entry:
                        assert value == location_to_entry[location]
                    else:
                        location_to_entry[location] = value
            # These are internal locations of an answer, so a heavy bar isn't needed.
            (left_bars if clue.is_across else top_bars).difference_update(
                (clue.location(i) for i in range(1, clue.length)))

        self.draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                       top_bars, left_bars, **more_args)

    def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                  location_to_entry: Dict[Location, str],
                  location_to_clue_number: Dict[Location, str],
                  top_bars: Set[Location],
                  left_bars: Set[Location],
                  **more_args: Any) -> None:
        draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                  top_bars, left_bars, **more_args)
