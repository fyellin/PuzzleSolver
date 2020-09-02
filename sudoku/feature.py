import abc
from typing import Iterable, Tuple, Sequence, Any, List

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

    def draw(self, context: dict) -> None:
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
            dr, dc = descriptors[direction.upper().strip()]
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
    def draw_rectangles(points: Sequence[Tuple[int, int]], **args: Any):
        args = {'color': 'lightgrey', 'fill': True, **args}
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
