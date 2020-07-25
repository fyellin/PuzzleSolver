from __future__ import annotations

import abc
import functools
import itertools
from typing import Iterable, Tuple, Sequence, Any, Set, List, Optional, ClassVar

from matplotlib import pyplot as plt

from cell import Cell, House
from grid import Grid


class Feature(abc.ABC):
    def initialize(self, grid: Grid) -> None:
        pass

    def reset(self, grid: Grid) -> None:
        pass

    def get_neighbors(self, cell: Cell) -> Iterable[Cell]:
        return ()

    def get_neighbors_for_value(self, cell: Cell, value: int) -> Iterable[Cell]:
        return ()

    def check(self) -> bool:
        return False

    def check_special(self) -> bool:
        return False

    def draw(self) -> None:
        pass

    @staticmethod
    def neighbors_from_offsets(grid: Grid, cell: Cell, offsets: Iterable[Tuple[int, int]]) -> Iterable[Cell]:
        row, column = cell.index
        for dr, dc in offsets:
            if 1 <= row + dr <= 9 and 1 <= column + dc <= 9:
                yield grid.matrix[row + dr, column + dc]

    __DESCRIPTORS = dict(N=(-1, 0), S=(1, 0), E=(0, 1), W=(0, -1), NE=(-1, 1), NW=(-1, -1), SE=(1, 1), SW=(1, -1))

    @staticmethod
    def parse_line(descriptor: str) -> Sequence[Tuple[int, int]]:
        descriptors = Feature.__DESCRIPTORS
        pieces = descriptor.split(',')
        last_piece_row, last_piece_column = int(pieces[0]), int(pieces[1])
        squares = [(last_piece_row, last_piece_column)]
        for direction in pieces[2:]:
            dr, dc = descriptors[direction.upper()]
            last_piece_row += dr
            last_piece_column += dc
            squares.append((last_piece_row, last_piece_column))
        return squares

    @staticmethod
    def draw_line(points: Sequence[Tuple[int, int]], *, closed: bool = False, **kwargs: Any) -> None:
        ys = [row + .5 for row, _ in points]
        xs = [column + .5 for _, column in points]
        if closed:
            ys.append(ys[0])
            xs.append(xs[0])
        plt.plot(xs, ys, **{'color': 'black', **kwargs})


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


class PossibilitiesFeature(Feature):
    """We are given a set of possible values for a set of cells"""
    name: str
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]
    initial_possibilities: List[Tuple[Set[int], ...]]
    possibilities: List[Tuple[Set[int], ...]]
    handle_neighbors: bool

    def __init__(self, name: str, squares: Sequence[Tuple[int, int]],
                 possibilities: Iterable[Tuple[Set[int], ...]], *, neighbors: bool = False) -> None:
        self.name = name
        self.squares = squares
        self.initial_possibilities = list(possibilities)
        self.handle_neighbors = neighbors

    def initialize(self, grid: Grid) -> None:
        self.cells = [grid.matrix[square] for square in self.squares]

    def reset(self, grid: Grid) -> None:
        self.possibilities = self.initial_possibilities
        if self.handle_neighbors:
            self.__fix_possibilities_for_neighbors()
        self.__update_for_possibilities(False)

    def check(self) -> bool:
        old_length = len(self.possibilities)
        if old_length == 1:
            return False

        # Only keep those possibilities that are still available
        def is_viable(possibility: Tuple[Set[int], ...]) -> bool:
            return all(value.intersection(square.possible_values) for (value, square) in zip(possibility, self.cells))

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
        return (PossibilitiesFeature.fix_possibility(possibility) for possibility in possibilities)

    def __is_possibile(self, possibility: Tuple[Set[int], ...]) -> bool:
        return all(value.intersection(square.possible_values) for (value, square) in zip(possibility, self.cells))

    def __fix_possibilities_for_neighbors(self) -> None:
        possibilities = self.possibilities
        for (index1, cell1), (index2, cell2) in itertools.combinations(enumerate(self.cells), 2):
            if cell1.is_neighbor(cell2):
                possibilities = [p for p in possibilities if p[index1] != p[index2]]
        self.possibilities = possibilities


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
        super().__init__(f'magic square at {center}', squares, self.fix_possibilities(self.POSSIBILITES))
        self.color = color
        self.center = center

    def draw(self) -> None:
        axes = plt.gca()
        for (row, column) in self.squares:
            axes.add_patch(plt.Rectangle((column, row), width=1, height=1, fill=True, facecolor=self.color))


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

    def __is_impossible_value(self, value: int, previous_cell: Cell, cell: Cell, next_cell: Cell) -> bool:
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

    def draw(self) -> None:
        self.draw_line(self.squares, closed=self.cyclic, color=self.color, linewidth=5)


class AllValuesPresentFeature(Feature):
    """Verifies that within a set of squares, all values from 1 to 9 are present"""
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

    def draw(self) -> None:
        _draw_thermometer(self, self.squares, self.color)


class Thermometer2Feature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    color: str

    def __init__(self, name: str, thermometer: Sequence[Tuple[int, int]],  *, color: str = 'lightgrey'):
        super().__init__(name, thermometer, self.get_possibilities(len(thermometer)))
        self.color = color

    def draw(self) -> None:
        _draw_thermometer(self, self.squares, self.color)

    @classmethod
    def get_possibilities(cls, length: int) -> Iterable[Tuple[Set[int], ...]]:
        return cls.fix_possibilities(itertools.combinations(range(1, 10), length))


class Thermometer3Feature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    color: str

    def __init__(self, name: str, thermometer: Sequence[Tuple[int, int]], color: str = 'lightgrey'):
        super().__init__(name, thermometer, self.get_possibilities(len(thermometer)))
        self.color = color

    def draw(self) -> None:
        _draw_thermometer(self, self.squares, self.color)

    @classmethod
    def get_possibilities(cls, length: int) -> Iterable[Tuple[Set[int], ...]]:
        if length > 2:
            for permutation in itertools.combinations(range(2, 9), length - 2):
                yield (set(range(1, permutation[0])),
                       *cls.fix_possibility(permutation),
                       set(range(permutation[-1] + 1, 10)))
        else:
            for i in range(1, 9):
                yield {i}, set(range(1 + 1, 10))


class ThermometerFeature(Thermometer3Feature):
    pass


class SlowThermometerFeature(Thermometer1Feature):
    def match(self, digit1: int, digit2: int) -> bool:
        return digit1 <= digit2


class SnakeFeature(Feature):
    count: ClassVar[int] = 0

    """A set of nine squares where each number is used exactly once."""
    squares: Sequence[Tuple[int, int]]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def initialize(self, grid: Grid) -> None:
        cells = [grid.matrix[square] for square in self.squares]
        grid.houses.append(House(House.Type.EXTRA, 0, cells))

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


class LimitedValuesFeature(Feature):
    """A set of squares that can't contain all possible values"""
    squares: Sequence[Tuple[int, int]]
    values: Sequence[int]

    def __init__(self, squares: Sequence[Tuple[int, int]], values: Sequence[int]):
        self.squares = squares
        self.values = values

    def reset(self, grid: Grid) -> None:
        cells = [grid.matrix[x] for x in self.squares]
        Cell.keep_values_for_cell(cells, self.values)

    def check(self) -> bool:
        pass


class SameValueAsFeature(Feature, abc.ABC):
    main_square: Tuple[int, int]
    squares: Sequence[Tuple[int, int]]
    main_cell: Cell
    cells: Sequence[Cell]
    done: bool

    def __init__(self, main_square: Tuple[int, int], squares: Optional[Sequence[Tuple[int, int]]] = None):
        if squares is None:
            (r, c) = main_square
            squares = [(r + dr, c + dc) for dx in (-1, 1) for dy in (-2, 2)
                       for (dr, dc) in ((dx, dy), (dy, dx))
                       if 1 <= r + dr <= 9 and 1 <= c + dc <= 9]
        self.main_square = main_square
        self.squares = squares

    def initialize(self, grid: Grid) -> None:
        self.main_cell = grid.matrix[self.main_square]
        self.cells = [grid.matrix[x] for x in self.squares]
        self.done = False

    def check(self) -> bool:
        if self.done:
            return False
        if self.main_cell.is_known:
            assert self.main_cell.known_value is not None
            return self._check_value_known(self.main_cell.known_value)
        else:
            return self._check_value_not_known()

    @abc.abstractmethod
    def _check_value_known(self, value: int) -> bool: ...

    @abc.abstractmethod
    def _check_value_not_known(self) -> bool: ...


class SameValueAsExactlyOneMateFeature(SameValueAsFeature):
    def _check_value_known(self, value: int) -> bool:
        # We must make sure that the known value has exactly one mate
        count = sum(1 for cell in self.cells if cell.is_known and cell.known_value == value)
        mates = [cell for cell in self.cells if not cell.is_known and value in cell.possible_values]
        assert count < 2
        if count == 1:
            self.done = True
            if mates:
                print(f'Cell {self.main_square} already has a mate')
                Cell.remove_value_from_cells(mates, value)
                return True
            return False
        elif len(mates) == 1:
            print(f'Cell {self.main_square} only has one possible mate')
            mates[0].set_value_to(value, show=True)
            self.done = True
            return True
        return False

    def _check_value_not_known(self) -> bool:
        # The only possible values for this cell are those values for which it can have one mate.
        impossible_values = set()
        for value in self.main_cell.possible_values:
            count = sum(1 for cell in self.cells if cell.is_known and cell.known_value == value)
            mates = [cell for cell in self.cells if not cell.is_known and value in cell.possible_values]
            if count >= 2 or (count == 0 and not mates):
                impossible_values.add(value)
        if impossible_values:
            print(f'Cell {self.main_square} must have a matable value')
            Cell.remove_values_from_cells([self.main_cell], impossible_values)
            return True
        return False


class SameValueAsAtLeastOneMateFeature(SameValueAsFeature):
    def _check_value_known(self, value: int) -> bool:
        if any(cell.is_known and cell.known_value == value for cell in self.cells):
            self.done = True
            return False
        mates = [cell for cell in self.cells if not cell.is_known and value in cell.possible_values]
        assert len(mates) >= 1
        if len(mates) == 1:
            print(f'Cell {self.main_square} only has one possible mate')
            mates[0].set_value_to(value, show=True)
            self.done = True
            return True
        return False

    def _check_value_not_known(self) -> bool:
        legal_values = set.union(*(cell.possible_values for cell in self.cells))
        if not self.main_cell.possible_values <= legal_values:
            print(f'Cell {self.main_square} must must have a mate')
            Cell.keep_values_for_cell([self.main_cell], legal_values)
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

    def draw(self) -> None:
        colors = ('lightcoral', "violet", "bisque", "lightgreen", "lightgray", "yellow", "skyblue",
                  "pink", "purple")
        # colors = ('tab:cyan', 'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
        #           'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', )
        for color, squarex in zip(colors, self.squares):
            for row, column in squarex:
                plt.gca().add_patch(plt.Rectangle((column, row), 1, 1, facecolor=color))
