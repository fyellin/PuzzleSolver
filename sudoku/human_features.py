from __future__ import annotations

import abc
import functools
import itertools
from collections import deque, defaultdict
import datetime
from typing import Iterable, Tuple, Sequence, Any, Set, List, Optional, ClassVar, Mapping, Dict
import numpy as np
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

    @staticmethod
    def draw_rectangles(points: Seqeunce[Tuple[int, int]], **args: Any):
        args = {'facecolor': 'lightgrey', 'fill': True, **args}
        axis = plt.gca()
        for row, column in points:
            axis.add_patch(plt.Rectangle((column, row), width=1, height=1, **args))

    @staticmethod
    def draw_outside(value: Any, htype: House.Type, row_or_column: int, *,
                     is_right: bool = False, padding: float = 0, **args: Any):
        args = {'fontsize': 20, 'weight': 'bold', **args}

        if htype == House.Type.ROW:
            if not is_right:
                plt.text(.9 - padding, row_or_column + .5, str(value),
                         verticalalignment='center', horizontalalignment='right', **args)
            else:
                plt.text(10.1 + padding, row_or_column + .5, str(value),
                         verticalalignment='center', horizontalalignment='left', **args)
        else:
            if not is_right:
                plt.text(row_or_column + .5, .9 - padding, str(value),
                         verticalalignment='bottom', horizontalalignment='center', **args)
            else:
                plt.text(row_or_column + .5, 10.1 + padding, str(value),
                         verticalalignment='top', horizontalalignment='center', **args)

    @staticmethod
    def draw_outline(squares: Sequence[Tuple[int, int]], *, inset: float = .1, **args: Any) -> None:
        args = {'color': 'black', 'linewidth': 2, 'linestyle': "dotted", **args}
        squares_set = set(squares)

        # A wall is identified by the square it is in, and the direction you'd be facing from the center of that
        # square to see the wall.  A wall separates a square inside of "squares" from a square out of it.
        walls = {(row, column, dr, dc)
                 for row, column in squares for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0))
                 if (row + dr, column + dc) not in squares_set}

        while walls:
            start_wall = current_wall = next(iter(walls))  # pick some wall
            points: List[np.ndarray] = []

            while True:
                # Find the connecting point between the current wall and the wall to the right and add it to our
                # set of points

                row, column, ahead_dr, ahead_dc = current_wall  # square, and direction of wall from center
                right_dr, right_dc = ahead_dc, -ahead_dr  # The direction if we turned right

                # Three possible next walls, in order of preference.
                #  1) The wall makes a right turn, staying with the current square
                #  2) The wall continues in its direction, going into the square to our right
                #  3) The wall makes a left turn, continuing in the square diagonally ahead to the right.
                next1 = (row, column, right_dr, right_dc)   # right
                next2 = (row + right_dr, column + right_dc, ahead_dr, ahead_dc)  # straight
                next3 = (row + right_dr + ahead_dr, column + right_dc + ahead_dc, -right_dr, -right_dc)  # left

                # It is possible for next1 and next3 to both be in walls if we have two squares touching diagonally.
                # In that case, we prefer to stay within the same cell, so we prefer next1 to next3.
                next_wall = next(x for x in (next1, next2, next3) if x in walls)
                walls.remove(next_wall)

                if next_wall == next2:
                    # We don't need to add a point if the wall is continuing in the direction it was going.
                    pass
                else:
                    np_center = np.array((row, column)) + .5
                    np_ahead = np.array((ahead_dr, ahead_dc))
                    np_right = np.array((right_dr, right_dc))
                    right_inset = inset if next_wall == next1 else -inset
                    points.append(np_center + (.5 - inset) * np_ahead + (.5 - right_inset) * np_right)

                if next_wall == start_wall:
                    break
                current_wall = next_wall

            points.append(points[0])
            pts = np.vstack(points)
            plt.plot(pts[:, 1], pts[:, 0], **args)

    @staticmethod
    def get_row_or_column(htype, row_column):
        if htype == House.Type.ROW:
            squares = [(row_column, i) for i in range(1, 10)]
        else:
            squares = [(i, row_column) for i in range(1, 10)]
        return squares


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
        if self.handle_neighbors:
            self.__fix_possibilities_for_neighbors()
        print(f'{self.name} has {len(self.initial_possibilities)} possibilities')

    @abc.abstractmethod
    def get_possibilities(self) -> List[Tuple[Set[int], ...]]: ...

    def reset(self, grid: Grid) -> None:
        self.possibilities = list(self.initial_possibilities)
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
        super().__init__(f'magic square at {center}', squares)
        self.color = color
        self.center = center

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        return self.fix_possibilities(self.POSSIBILITES)

    def draw(self) -> None:
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
        super().__init__(name, thermometer)
        self.color = color

    def draw(self) -> None:
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

    def draw(self) -> None:
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
                yield {i}, set(range(1 + 1, 10))


class ThermometerFeature(Thermometer3Feature):
    pass


class SlowThermometerFeature(Thermometer1Feature):
    def match(self, digit1: int, digit2: int) -> bool:
        return digit1 <= digit2


class SnakeFeature(Feature):
    count: ClassVar[int] = 0
    my_number: int

    """A set of nine squares where each number is used exactly once."""
    squares: Sequence[Tuple[int, int]]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        SnakeFeature.count += 1
        self.my_number = SnakeFeature.count
        self.squares = squares

    @staticmethod
    def major_diagonal() -> SnakeFeature:
        return SnakeFeature([(i, i) for i in range(1, 10)])

    @staticmethod
    def minor_diagonal() -> SnakeFeature:
        return SnakeFeature([(10 - i, i) for i in range(1, 10)])

    def initialize(self, grid: Grid) -> None:
        cells = [grid.matrix[square] for square in self.squares]
        grid.houses.append(House(House.Type.EXTRA, 0, cells))

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)


class LimitedValuesFeature(Feature):
    """A set of squares that can't contain all possible values"""
    squares: Sequence[Tuple[int, int]]
    values: Sequence[int]

    def __init__(self, squares: Sequence[Tuple[int, int]], values: Sequence[int]):
        self.squares = squares
        self.values = values

    def reset(self, grid: Grid) -> None:
        cells = [grid.matrix[x] for x in self.squares]
        Cell.keep_values_for_cell(cells, set(self.values))

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
        for squarex, color in zip(self.squares, colors):
            self.draw_outline(squarex, color=color, inset=.1)


class SandwichFeature(PossibilitiesFeature):
    htype: House.Type
    row_column: int
    total: int

    def __init__(self, htype: House.Type, row_column: int, total: int):
        name = f'Sandwich {htype.name.title()} #{row_column}'
        squares = self.get_row_or_column(htype, row_column)
        self.htype = htype
        self.row_column = row_column
        self.total = total
        super().__init__(name, squares, compressed=True)

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

    def draw(self) -> None:
        self.draw_outside(self.total, self.htype, self.row_column, fontsize=20, weight='bold')


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

    def draw(self) -> None:
        args = dict(fontsize=20, weight='bold')
        self.draw_outside(self.value, self.htype, self.row_column, is_right=self.is_right, **args)
