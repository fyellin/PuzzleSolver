import itertools
from typing import Tuple, Sequence,  Dict, List

from matplotlib import pyplot as plt

from solver import DancingLinks


class Sudoku:
    initial_grid: Dict[Tuple[int, int], int]

    def solve(self, puzzle: str, *,
              king: bool = False, knight: bool = False, adjacent: bool = False,
              magic: bool = False,
              thermometers: Sequence[Sequence[Tuple[int, int]]] = (),
              evens: Sequence[Tuple[int, int]] = (),
              snakes: Sequence[Tuple[int, int]] = ()) -> None:

        initial_grid = {(row, column): int(letter)
                               for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                               if '1' <= letter <= '9'}
        self.initial_grid = initial_grid

        def row_printer(results: Sequence[Tuple[int, int, int]]) -> None:
            self.draw_grid(initial_grid, results)

        constraints = self.__get_default_constraints()
        optional_constraints = set()

        deletions = {(row, column, valuex)
                     for (row, column), value in initial_grid.items()
                     for valuex in range(1, 10) if valuex != value }

        def impossible(triple1: Tuple[int, int, int], triple2: Tuple[int, int, int], name: str = ''):
            row1, column1, value1 = triple1
            row2, column2, value2 = triple2
            constraint = f'{name}:r{row1}c{column1}={value1};r{row2}c{column2}={value2}'
            optional_constraints.add(constraint)
            constraints[row1, column1, value1].append(constraint)
            constraints[row2, column2, value2].append(constraint)

        for row, column in itertools.product(range(1, 10), repeat=2):
            if knight or king:
                neighbors = set()
                if knight:
                    neighbors.update(self.knights_move(row, column))
                if king:
                    neighbors.update(self.kings_move(row, column))
                # For each "neighbor", we add an optional constraint so that either this cell can have a value or the
                # neighbor can have the value.  This ensures that at most one of them will have the specified value
                for neighbor_row, neighbor_column in neighbors:
                    if (row, column) < (neighbor_row, neighbor_column):
                        for value in range(1, 10):
                            impossible((row, column, value), (neighbor_row, neighbor_column, value), 'C')

            if adjacent:
                # For each cell next me me, create an optional constraint such that if I have a specific value,
                # the neighbor cannot have one more than that value.
                for neighbor_row, neighbor_column in self.adjacent_move(row, column):
                    for value in range(1, 9):  # Note, we don't need to use value=9.
                        impossible((row, column, value), (neighbor_row, neighbor_column, value + 1))

        for thermo_index, thermometer in enumerate(thermometers, start=2):
            length = len(thermometer)
            span = 10 - length  # number of values each element in thermometer can have
            for minimum, (row, column) in enumerate(thermometer, start=1):
                maximum = minimum + span - 1
                deletions.update((row, column, value) for value in range(1, 10) if not minimum <= value <= maximum)
            prefix = f'T{thermo_index}'
            for (index1, (row1, col1)), (index2, (row2, col2)) in itertools.combinations(enumerate(thermometer), 2):
                for value1, value2 in itertools.product(range(1, 10), repeat=2):
                    if value2 < value1 + (index2 - index1):
                        impossible((row1, col1, value1), (row2, col2, value2), prefix)

        if magic:
            deltas = ((-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))
            values = (2, 9, 4, 3, 8, 1, 6, 7)

            for center_x, center_y in ((2, 6), (4, 2), (6, 8), (8, 4)):
                squares = [(center_x + delta_x, center_y + delta_y) for delta_x, delta_y in deltas]

                # The center must be five, the corners must be even, and the others must be odd.
                deletions.update((center_x, center_y, value) for value in range(1, 10) if value != 5)
                deletions.update((row, column, value) for (row, column) in squares[0::2] for value in (1, 3, 5, 7, 9))
                deletions.update((row, column, value) for (row, column) in squares[1::2] for value in (2, 4, 5, 6, 8))

                for (i1, (row1, col1)), (i2, (row2, col2)) in itertools.combinations(enumerate(squares), 2):
                    delta = i2 - i1
                    for value_index in (0, 2, 4, 6):
                        value1 = values[(value_index + i1) % 8]
                        value2a = values[(value_index + i1 + delta) % 8]
                        value2b = values[(value_index + i1 - delta) % 8]
                        for value2 in range(1, 10):
                            if value2 != value2a and value2 != value2b:
                                impossible((row1, col1, value1), (row2, col2, value2), f'MS{center_x}{center_y}')

        if self is None:
            # This handles the cups, in which certain squares had to differ by 5 or more
            cup1 = ((1, 2), (2, 2), (3, 3), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (8, 3))
            cup2 = tuple((row, 10 - column) for row, column in cup1)
            deletions.update((row, column, 5) for cup in (cup1, cup2) for row, column in cup)
            for cup in (cup1, cup2):
                for ((row1, col1), (row2, col2)) in zip(cup, cup[1:]):
                    for value1, value2 in itertools.product(range(1, 10), repeat=2):
                        if abs(value1 - value2) < 5:
                            impossible((row1, col1, value1), (row2, col2, value2))

        if self is None:
            # This handled a circle, in which adjacent values had to add to a square or cube, and there had to be one
            # of every digit in the circle
            square = ((2, 4), (2, 5), (2, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 7),
                      (8, 6), (8, 5), (8, 4), (7, 3), (6, 2), (5, 2), (4, 2), (3, 3))
            for ((row1, col1), (row2, col2)) in zip(square, square[1:] + square[:1]):
                for value1, value2 in itertools.product(range(1, 10), repeat=2):
                    if value1 + value2 not in (1, 4, 8, 9, 16):
                        impossible((row1, col1, value1), (row2, col2, value2), 'c')

            def row_printer(results: Sequence[Tuple[int, int, int]]) -> None:
                values = {value for (row, column, value) in results if (row, column) in square}
                if len(values) == 9:
                    self.draw_grid(initial_grid, results)

        for i, snake in enumerate(snakes):
            for value in range(1, 10):
                constraint = f"Snake{i}={value}"
                # If the snake has length 9, each of the constraints will be fulfilled.  Otherwise, they're optional.
                if len(snake) < 9:
                    optional_constraints.add(constraint)
                for row, column in snake:
                    constraints[row, column, value].append(constraint)

        if evens:
            deletions.update((row, column, value) for row, column in self.evens for value in (1, 3, 5, 7, 9))

        for key in deletions:
            constraints.pop(key)

        links = DancingLinks(constraints, optional_constraints=optional_constraints, row_printer=row_printer)
        links.solve(debug=1000, recursive=False,)


    @staticmethod
    def knights_move(row: int, column: int) -> Sequence[Tuple[int, int]]:
        return [((row + dr), (column + dc))
                for dx, dy in itertools.product((1, -1), (2, -2))
                for dr, dc in ((dx, dy), (dy, dx))
                if 1 <= row + dr <= 9 and 1 <= column + dc <= 9]

    @staticmethod
    def kings_move(row: int, column: int) -> Sequence[Tuple[int, int]]:
        return [((row + dr), (column + dc))
                for dr, dc in itertools.product((-1, 1), repeat=2)
                if 1 <= row + dr <= 9 and 1 <= column + dc <= 9]

    @staticmethod
    def adjacent_move(row: int, column: int) -> Sequence[Tuple[int, int]]:
        return [((row + dr), (column + dc))
                for dx in (-1, 1)
                for dr, dc in ((dx, 0), (0, dx))
                if 1 <= row + dr <= 9 and 1 <= column + dc <= 9]

    @staticmethod
    def draw_grid(initial_grid, results: Sequence[Tuple[int, int, int]]) -> None:
        figure, axes = plt.subplots(1, 1, figsize=(4, 4), dpi=100)

        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([1, 10, 10, 1])
        axes.axis('equal')
        axes.axis('off')
        figure.tight_layout()

        # Draw the bold outline
        for x in range(1, 11):
            width = 3 if x in (1, 4, 7, 10) else 1
            axes.plot([x, x], [1, 10], linewidth=width, color='black')
            axes.plot([1, 10], [x, x], linewidth=width, color='black')

        given = dict(fontsize=13, color='black', weight='heavy')
        found = dict(fontsize=12, color='blue', weight='normal')
        for row, column, value in results:
            args = given if (row, column) in initial_grid else found
            axes.text(column + .5, row + .5, str(value),
                      verticalalignment='center', horizontalalignment='center', **args)
        plt.show()

    @staticmethod
    def __get_default_constraints() -> Dict[Tuple[int, int, int], List[str]]:
        def box(row: int, column: int) -> int:
            return row - (row - 1) % 3 + (column - 1) // 3

        return {(row, column, value):
                    [f"V{row}{column}", f"R{row}={value}", f"C{column}={value}", f"B{box(row, column)}={value}"]
                for row, value, column in itertools.product(range(1, 10), repeat=3)
                }

def merge(p1: str, p2: str):
    assert len(p1) == len(p2) == 81
    assert(p1[i] == '.' or p2[i] == '.' or p1[i] == p2[i] for i in range(81))
    result = ((y if x == '.' else x) for x, y in zip(p1, p2))
    return ''.join(result)


def main() -> None:
    # XUZZ = "123456789123456789123456789123456789123456789123456789123456789123456789123456789"
    PUZZLE = ".................1.......................................................6......."
    Sudoku().solve(PUZZLE, magic=True)

    # PREVIO = "..7......3.....5......................3..8............15.............9....9......"
    # PUZZLE = "......3...1...............72.........................2..................8........"
    #
    # thermometers = [[(row, column) for row in (9, 8, 7, 6, 5, 4)] for column in (2, 4, 6, 8)]
    # snake = ((1, 4), (1, 6), (2, 1), (2, 9), (3, 3), (3, 5), (3, 7), (4, 2), (4, 8))
    # Sudoku().solve(merge(PUZZLE, PREVIO), thermometers=thermometers, snake=snake)

if __name__ == '__main__':
    main()
