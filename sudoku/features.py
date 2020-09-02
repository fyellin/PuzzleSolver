from __future__ import annotations

import abc
import functools
import itertools
from collections import deque, defaultdict
import datetime
from typing import Iterable, Tuple, Sequence, Set, List, Optional, ClassVar, Mapping, Dict
from matplotlib import pyplot as plt

from cell import Cell, House
from feature import Feature
from grid import Grid


class KnightsMoveFeature(Feature):
    """No two squares within a knight's move of each other can have the same value."""
    OFFSETS = [(dr, dc) for dx in (-1, 1) for dy in (-2, 2) for (dr, dc) in ((dx, dy), (dy, dx))]
    grid: Grid

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def get_neighbors(self, cell: Cell) -> Iterable[Cell]:
        return self.neighbors_from_offsets(self.grid, cell, self.OFFSETS)


class KingsMoveFeature(Feature):
    """No two pieces within a king's move of eachother can have the same value."""
    OFFSETS = [(dr, dc) for dr in (-1, 1) for dc in (-1, 1)]
    grid: Grid

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def get_neighbors(self, cell: Cell) -> Iterable[Cell]:
        return self.neighbors_from_offsets(self.grid, cell, self.OFFSETS)


class QueensMoveFeature(Feature):
    OFFSETS = [(dr, dc) for delta in range(1, 9) for dr in (-delta, delta) for dc in (-delta, delta)]
    grid: Grid
    values: Set[int]

    def __init__(self, values: Set[int] = frozenset({9})):
        self.values = values

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def get_neighbors_for_value(self, cell: Cell, value: int) -> Iterable[Cell]:
        if value in self.values:
            return self.neighbors_from_offsets(self.grid, cell, self.OFFSETS)
        else:
            return ()


class TaxicabFeature(Feature):
    """Two squares with the same value cannot have "value" as the taxicab distance between them."""
    grid: Grid
    taxis: Set[int]

    def __init__(self, taxis: Sequence[int] = ()):
        self.taxis = set(taxis)

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def get_neighbors_for_value(self, cell: Cell, value: int) -> Iterable[Cell]:
        if value in self.taxis:
            offsets = self.__get_offsets_for_value(value)
            return self.neighbors_from_offsets(self.grid, cell, offsets)
        else:
            return ()

    @staticmethod
    @functools.lru_cache()
    def __get_offsets_for_value(value: int) -> Sequence[Tuple[int, int]]:
        result = [square for i in range(0, value)
                  for square in [(i - value, i), (i, value - i), (value - i, -i), (-i, i - value)]]
        return result


class PossibilitiesFeature(Feature, abc.ABC):
    """We are given a set of possible values for a set of cells"""
    name: str
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]
    initial_possibilities: List[Tuple[Set[int], ...]]
    possibilities: List[Tuple[Set[int], ...]]
    handle_neighbors: bool
    compressed: bool

    def __init__(self, name: str, squares: Sequence[Tuple[int, int]], *,
                 neighbors: bool = False, compressed: bool = False) -> None:
        self.name = name
        self.squares = squares
        self.handle_neighbors = neighbors
        self.compressed = compressed

    def initialize(self, grid: Grid) -> None:
        self.cells = [grid.matrix[square] for square in self.squares]
        self.initial_possibilities = list(self.get_possibilities())
        print(f'{self.name} has {len(self.initial_possibilities)} possibilities')

    @abc.abstractmethod
    def get_possibilities(self) -> List[Tuple[Set[int], ...]]: ...

    def reset(self, grid: Grid) -> None:
        self.possibilities = list(self.initial_possibilities)
        if self.handle_neighbors:
            self.possibilities = self.__fix_possibilities_for_neighbors(self.possibilities)
        self.__update_for_possibilities(False)

    def check(self) -> bool:
        old_length = len(self.possibilities)
        if old_length == 1:
            return False

        # Only keep those possibilities that are still available
        def is_viable(possibility: Tuple[Set[int], ...]) -> bool:
            choices = [value.intersection(square.possible_values) for (value, square) in zip(possibility, self.cells)]
            if not all(choices):
                return False
            if self.compressed:
                open_choices = [choice for choice, cell in zip(choices, self.cells) if not cell.is_known]
                for length in range(2, len(open_choices)):
                    for subset in itertools.combinations(open_choices, length):
                        if len(set.union(*subset)) < length:
                            return False
            return True

        self.possibilities = list(filter(is_viable, self.possibilities))
        if len(self.possibilities) < old_length:
            print(f"Possibilities for {self.name} reduced from {old_length} to {len(self.possibilities)}")
            return self.__update_for_possibilities()
        return False

    def __update_for_possibilities(self, show: bool = True) -> bool:
        updated = False
        for index, cell in enumerate(self.cells):
            if cell.is_known:
                continue
            legal_values = set.union(*[possibility[index] for possibility in self.possibilities])
            if not cell.possible_values <= legal_values:
                updated = True
                Cell.keep_values_for_cell([cell], legal_values, show=show)
        return updated

    def __repr__(self) -> str:
        return f'<{self.name}>'

    @staticmethod
    def fix_possibility(possibility: Tuple[int, ...]) -> Tuple[Set[int], ...]:
        return tuple({p} for p in possibility)

    @staticmethod
    def fix_possibilities(possibilities: Iterable[Tuple[int, ...]]) -> Iterable[Tuple[Set[int], ...]]:
        return map(PossibilitiesFeature.fix_possibility, possibilities)

    def __is_possibile(self, possibility: Tuple[Set[int], ...]) -> bool:
        return all(value.intersection(square.possible_values) for (value, square) in zip(possibility, self.cells))

    def __fix_possibilities_for_neighbors(self, possibilities: Sequence[Tuple[Set[int], ...]]) -> Sequence[Tuple[Set[int], ...]] :
        for (index1, cell1), (index2, cell2) in itertools.combinations(enumerate(self.cells), 2):
            if cell1.is_neighbor(cell2):
                possibilities = [p for p in possibilities if len(p[index1]) > 1 or p[index1] != p[index2]]
            elif cell1.index == cell2.index:
                #  We're not sure if this works or not
                possibilities = [p for p in possibilities if p[index1] == p[index2]]
        return possibilities


class MultiPossibilityFeature(PossibilitiesFeature):
    possibility_features: Sequence[PossibilitiesFeature]
    def __init__(self, possibility_features: Sequence[PossibilityFeature]):
        squares = [x for possibility in possibility_features for x in possibility.squares]
        super().__init__("MultiFeature", squares, neighbors=True, compressed=True)
        self.possibility_features = possibility_features

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        possiblity_list_list = [list(possibility.get_possibilities()) for possibility in self.possibility_features]
        for results in itertools.product(*possiblity_list_list):
            temp = tuple(x for result in results for x in result)
            yield temp

    def draw(self, context: dict):
        for possibility in self.possibility_features:
            possibility.draw(dict())


class MagicSquareFeature(PossibilitiesFeature):
    """There is a magic square within the grid"""
    POSSIBILITES = ((2, 7, 6, 9, 5, 1, 4, 3, 8), (2, 9, 4, 7, 5, 3, 6, 1, 8),
                    (8, 3, 4, 1, 5, 9, 6, 7, 2), (8, 1, 6, 3, 5, 7, 4, 9, 2),
                    (4, 3, 8, 9, 5, 1, 2, 7, 6), (6, 1, 8, 7, 5, 3, 2, 9, 4),
                    (6, 7, 2, 1, 5, 9, 8, 3, 4), (4, 9, 2, 3, 5, 7, 8, 1, 6),)

    center: Tuple[int, int]
    color: str

    def __init__(self, center: Tuple[int, int] = (5, 5), *, dr: int = 1, dc: int = 1, color: str = 'lightblue'):
        center_x, center_y = center
        squares = [(center_x + dr * dx, center_y + dc * dy) for dx, dy in itertools.product((-1, 0, 1), repeat=2)]
        super().__init__(f'magic square at {center}', squares)
        self.color = color
        self.center = center

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        return self.fix_possibilities(self.POSSIBILITES)

    def draw(self, context: dict) -> None:
        axes = plt.gca()
        self.draw_rectangles(self.squares, facecolor=self.color)


class AdjacentRelationshipFeature(Feature, abc.ABC):
    """
    Adjacent squares must fulfill some relationship.

    The squares have an order, so this relationship does not need to be symmetric.  (I.e. a thermometer)
    """
    name: str
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]
    cyclic: bool
    handle_reset: bool

    triples: Sequence[Tuple[Optional[Cell], Cell, Optional[Cell]]]
    color: str

    def __init__(self, name: str, squares: Sequence[Tuple[int, int]], *,
                 cyclic: bool = False, reset: bool = False, color: str = 'gold'):
        self.name = name
        self.squares = squares
        self.cyclic = cyclic
        self.handle_reset = reset
        self.color = color

    def initialize(self, grid: Grid) -> None:
        self.cells = [grid.matrix[x] for x in self.squares]
        self.triples = [
            ((self.cells[-1] if self.cyclic else None), self.cells[0], self.cells[1]),
            *[(self.cells[i - 1], self.cells[i], self.cells[i + 1]) for i in range(1, len(self.cells) - 1)],
            (self.cells[-2], self.cells[-1], (self.cells[0] if self.cyclic else None))]

    def reset(self, grid: Grid) -> None:
        if self.handle_reset:
            while self.check(show=False):
                pass

    @abc.abstractmethod
    def match(self, digit1: int, digit2: int) -> bool: ...

    def check(self, show: bool = True) -> bool:
        for previous_cell, cell, next_cell in self.triples:
            if cell.is_known:
                continue
            impossible_values = {value for value in cell.possible_values
                                 if self.__is_impossible_value(value, previous_cell, cell, next_cell)}
            if impossible_values:
                if show:
                    print("No appropriate value in adjacent cells")
                Cell.remove_values_from_cells([cell], impossible_values, show=show)
                return True
        return False

    def __is_impossible_value(self, value: int,
                              previous_cell: Optional[Cell], cell: Cell, next_cell: Optional[Cell]) -> bool:
        previous_match = next_match = set(range(1, 10))
        if previous_cell:
            previous_match = {value2 for value2 in previous_cell.possible_values if self.match(value2, value)}
            if cell.is_neighbor(previous_cell):
                previous_match.discard(value)
        if next_cell:
            next_match = {value2 for value2 in next_cell.possible_values if self.match(value, value2)}
            if cell.is_neighbor(next_cell):
                next_match.discard(value)
        if not previous_match or not next_match:
            return True
        elif previous_cell and next_cell and previous_cell.is_neighbor(next_cell) \
                and len(previous_match) == 1 and len(next_match) == 1 and previous_match == next_match:
            return True
        return False

    def draw(self, context: dict) -> None:
        self.draw_line(self.squares, closed=self.cyclic, color=self.color, linewidth=5)


class AllValuesPresentFeature(Feature):
    """Verifies that within a set of squares, all values from 1 to 9 are present.  There should be nine or more
    squares.

    You should probably be using a SnakeFeature if there are exactly nine squares, as other more complicated logic
    is available if there is precisely one of each number.
    """
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        assert len(squares) >= 9
        self.squares = squares

    def initialize(self, grid: Grid) -> None:
        self.cells = [grid.matrix[x] for x in self.squares]

    def check(self) -> bool:
        known_cell_values = {cell.known_value for cell in self.cells if cell.is_known}
        unknown_cell_values = [value for value in range(1, 10) if value not in known_cell_values]
        unknown_cells = {cell for cell in self.cells if not cell.is_known}
        result = False
        for value in unknown_cell_values:
            cells = [cell for cell in unknown_cells if value in cell.possible_values]
            assert len(cells) >= 1
            if len(cells) == 1:
                cells[0].set_value_to(value)
                print(f'Hidden Single: Ring = {value} must be {cells[0]}')
                result = True
        return result


def _draw_thermometer(feature: Feature, squares: Sequence[Tuple[int, int]], color: str) -> None:
    feature.draw_line(squares, color=color, linewidth=10)
    row, column = squares[0]
    plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor=color))


class Thermometer1Feature(AdjacentRelationshipFeature):
    """
    A sequence of squares that must monotomically increase.

    If slow is set, then this is a "slow" thermometer, and two adjacent numbers can be the same.  Typically,
    thermometers must be strictly monotonic.

    This implementation uses "adjacency"
    """
    def __init__(self, name: str, thermometer: Sequence[Tuple[int, int]], *, color: str = 'lightgrey') -> None:
        super().__init__(name, thermometer, reset=True, color=color)

    def match(self, digit1: int, digit2: int) -> bool:
        return digit1 < digit2

    def draw(self, context: dict) -> None:
        _draw_thermometer(self, self.squares, self.color)


class Thermometer2Feature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    color: str

    def __init__(self, name: str, thermometer: Sequence[Tuple[int, int]],  *, color: str = 'lightgrey'):
        super().__init__(name, thermometer)
        self.color = color

    def draw(self, context: dict) -> None:
        _draw_thermometer(self, self.squares, self.color)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        return self.fix_possibilities(itertools.combinations(range(1, 10), len(self.squares)))


class Thermometer3Feature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    color: str

    def __init__(self, name: str, thermometer: Sequence[Tuple[int, int]], color: str = 'lightgrey'):
        super().__init__(name, thermometer)
        self.color = color

    def draw(self, context: dict) -> None:
        _draw_thermometer(self, self.squares, self.color)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        length = len(self.squares)
        if length > 2:
            for permutation in itertools.combinations(range(2, 9), length - 2):
                yield (set(range(1, permutation[0])),
                       *self.fix_possibility(permutation),
                       set(range(permutation[-1] + 1, 10)))
        else:
            for i in range(1, 9):
                yield {i}, set(range(i + 1, 10))


class ThermometerFeature(Thermometer3Feature):
    pass


class SlowThermometerFeature(Thermometer1Feature):
    def match(self, digit1: int, digit2: int) -> bool:
        return digit1 <= digit2


class SnakeFeature(Feature):
    count: ClassVar[int] = 0
    my_number: int
    line: bool

    """A set of nine squares where each number is used exactly once."""
    squares: Sequence[Tuple[int, int]]

    def __init__(self, squares: Sequence[Tuple[int, int]], *, line: bool = True):
        SnakeFeature.count += 1
        assert len(squares) == 9
        self.my_number = SnakeFeature.count
        self.squares = squares
        self.line = line

    @staticmethod
    def major_diagonal() -> SnakeFeature:
        return SnakeFeature([(i, i) for i in range(1, 10)])

    @staticmethod
    def minor_diagonal() -> SnakeFeature:
        return SnakeFeature([(10 - i, i) for i in range(1, 10)])

    def initialize(self, grid: Grid) -> None:
        cells = [grid.matrix[square] for square in self.squares]
        grid.houses.append(House(House.Type.EXTRA, 0, cells))

    def draw(self, context: dict) -> None:
        if self.line:
            self.draw_line(self.squares, color='lightgrey', linewidth=5)
        else:
            for row, column in self.squares:
                plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.1, fill=True, facecolor='blue'))


class LimitedValuesFeature(Feature):
    """A set of squares that can't contain all possible values"""
    squares: Sequence[Tuple[int, int]]
    values: Sequence[int]
    color: Optional[str]

    def __init__(self, squares: Sequence[Tuple[int, int]], values: Sequence[int], *, color: Optional[str] = None):
        self.squares = squares
        self.values = values
        self.color = color

    def reset(self, grid: Grid) -> None:
        cells = [grid.matrix[x] for x in self.squares]
        Cell.keep_values_for_cell(cells, set(self.values), show=False)

    def check(self) -> bool:
        pass

    def draw(self, context: dict) -> None:
        if self.color:
            self.draw_rectangles(self.squares, color=self.color)


class AbstractMateFeature(Feature, abc.ABC):
    this_square: Tuple[int, int]
    this_cell: Cell
    possible_mates: Sequence[Cell]
    done: bool

    def __init__(self, square: Tuple[int, int]):
        self.this_square = square

    def initialize(self, grid: Grid) -> None:
        self.this_cell = grid.matrix[self.this_square]
        self.possible_mates = list(self.get_mates(self.this_cell, grid))
        self.done = False

    def get_mates(self, cell: Cell, grid: Grid) -> Iterable[Cell]:
        return self.neighbors_from_offsets(grid, cell, KnightsMoveFeature.OFFSETS)

    def check(self) -> bool:
        if self.done:
            return False
        if self.this_cell.is_known:
            assert self.this_cell.known_value is not None
            return self._check_value_known(self.this_cell.known_value)
        else:
            return self._check_value_not_known()

    @abc.abstractmethod
    def _check_value_known(self, value: int) -> bool: ...

    @abc.abstractmethod
    def _check_value_not_known(self) -> bool: ...


class SameValueAsExactlyOneMateFeature(AbstractMateFeature):
    def _check_value_known(self, value: int) -> bool:
        # We must make sure that the known value has exactly one mate
        count = sum(1 for cell in self.possible_mates if cell.is_known and cell.known_value == value)
        mates = [cell for cell in self.possible_mates if not cell.is_known and value in cell.possible_values]
        assert count < 2
        if count == 1:
            self.done = True
            if mates:
                print(f'Cell {self.this_cell} can only have one mate')
                Cell.remove_value_from_cells(mates, value)
                return True
            return False
        elif len(mates) == 1:
            print(f'Cell {self.this_cell} only has one possible mate')
            mates[0].set_value_to(value, show=True)
            self.done = True
            return True
        return False

    def _check_value_not_known(self) -> bool:
        # The only possible values for this cell are those values for which it can have one mate.
        impossible_values = set()
        for value in self.this_cell.possible_values:
            count = sum(1 for cell in self.possible_mates if cell.is_known and cell.known_value == value)
            mates = [cell for cell in self.possible_mates if not cell.is_known and value in cell.possible_values]
            if count >= 2 or (count == 0 and not mates):
                impossible_values.add(value)
        if impossible_values:
            print(f'Cell {self.this_cell} must have a matable value')
            Cell.remove_values_from_cells([self.this_cell], impossible_values)
            return True
        return False


class SameValueAsMateFeature(AbstractMateFeature):
    def _check_value_known(self, value: int) -> bool:
        if any(cell.is_known and cell.known_value == value for cell in self.possible_mates):
            # We didn't change anything, but we've verified that this guy has a mate
            self.done = True
            return False
        mates = [cell for cell in self.possible_mates if not cell.is_known and value in cell.possible_values]
        assert len(mates) >= 1
        if len(mates) == 1:
            print(f'Cell {self.this_cell} has only one possible mate')
            mates[0].set_value_to(value, show=True)
            self.done = True
            return True
        return False

    def _check_value_not_known(self) -> bool:
        legal_values = set.union(*(cell.possible_values for cell in self.possible_mates))
        if not self.this_cell.possible_values <= legal_values:
            print(f'Cell {self.this_cell} must have a mate')
            Cell.keep_values_for_cell([self.this_cell], legal_values)
            return True
        return False


class LittlePrincessFeature(Feature):
    grid: Grid

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def get_neighbors_for_value(self, cell: Cell, value: int) -> Iterable[Cell]:
        offsets = self.__get_offsets_for_value(value)
        return self.neighbors_from_offsets(self.grid, cell, offsets)

    @staticmethod
    @functools.lru_cache
    def __get_offsets_for_value(value: int) -> Sequence[Tuple[int, int]]:
        return [(dr, dc) for delta in range(1, value)
                for dr in (-delta, delta) for dc in (-delta, delta)]


class AlternativeBoxesFeature(Feature):
    squares: Sequence[List[Tuple[int, int]]]

    def __init__(self, pattern: str) -> None:
        assert len(pattern) == 81
        info: Sequence[List[Tuple[int, int]]] = [list() for _ in range(10)]
        for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), pattern):
            assert '1' <= letter <= '9'
            info[int(letter)].append((row, column))
        for i in range(1, 10):
            assert len(info[i]) == 9
        self.squares = info[1:]

    def initialize(self, grid: Grid) -> None:
        grid.delete_normal_boxes()
        boxes = [House(House.Type.BOX, i + 1,
                       [grid.matrix[square] for square in self.squares[i]])
                 for i in range(len(self.squares))]
        grid.houses.extend(boxes)

    def draw(self, context: dict) -> None:
        colors = ('lightcoral', "violet", "bisque", "lightgreen", "lightgray", "yellow", "skyblue",
                  "pink", "purple")
        for squarex, color in zip(self.squares, colors):
            self.draw_outline(squarex, color=color, inset=.1)


class SandwichFeature(PossibilitiesFeature):
    htype: House.Type
    row_column: int
    total: int
    grid: Grid

    def __init__(self, htype: House.Type, row_column: int, total: int):
        name = f'Sandwich {htype.name.title()} #{row_column}'
        squares = self.get_row_or_column(htype, row_column)
        self.htype = htype
        self.row_column = row_column
        self.total = total
        super().__init__(name, squares, compressed=True)

    def initialize(self, grid: Grid) -> None:
        self.grid = grid
        super().initialize(grid)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        return self._get_possibilities(self.total)

    @classmethod
    def _get_possibilities(cls, total: int) -> Iterable[Tuple[Set[int], ...]]:
        for length in range(0, 8):
            for values in itertools.combinations((2, 3, 4, 5, 6, 7, 8), length):
                if sum(values) == total:
                    non_values = set(range(2, 9)) - set(values)
                    non_values_length = 7 - length
                    temp = deque([{1, 9}, *([set(values)] * length), {1, 9}, *([non_values] * non_values_length)])
                    for i in range(0, non_values_length + 1):
                        yield tuple(temp)
                        temp.rotate(1)

    def draw(self, context: dict) -> None:
        self.draw_outside(self.total, self.htype, self.row_column, fontsize=20, weight='bold')
        if not context.get(self.__class__):
            context[self.__class__] = True
            special = [cell.index for cell in self.grid.cells if cell.possible_values.isdisjoint({1, 9})]
            self.draw_rectangles(special, color='lightgreen')

class SandwichXboxFeature(PossibilitiesFeature):
    htype: House.Type
    row_column: int
    value: int
    is_right: bool

    def __init__(self, htype: House.Type, row_column: int, value: int, right: bool = False) -> None:
        name = f'Skyscraper {htype.name.title()} #{row_column}'
        squares = self.get_row_or_column(htype, row_column)
        self.htype = htype
        self.row_column = row_column
        self.value = value
        self.is_right = right
        super().__init__(name, squares)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        result = self._get_all_possibilities()[self.value]
        if not self.is_right:
            return self.fix_possibilities(result)
        else:
            return self.fix_possibilities(item[::-1] for item in result)

    @staticmethod
    @functools.lru_cache(None)
    def _get_all_possibilities() -> Mapping[int, Sequence[Tuple[int, ...]]]:

        result: Dict[int, List[Tuple[int, ...]]] = defaultdict(list)
        start = datetime.datetime.now()
        for values in itertools.permutations(range(1, 10)):
            index1 = values.index(1)
            index2 = values.index(9)
            if index2 < index1:
                index2, index1 = index1, index2
            sandwich = sum([values[index] for index in range(index1 + 1, index2)])
            xbox = sum([values[index] for index in range(values[0])])
            if sandwich == xbox:
                result[sandwich].append(values)
        end = datetime.datetime.now()
        print(f'Initialization = {end - start}.')
        return result

    def draw(self, context: dict) -> None:
        args = dict(fontsize=20, weight='bold')
        self.draw_outside(self.value, self.htype, self.row_column, is_right=self.is_right, **args)
