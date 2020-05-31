import itertools
from collections import deque
from typing import Tuple, Sequence, Callable, Dict, List

from matplotlib import pyplot as plt

from solver import DancingLinks


class Sudoku:
    king: bool
    knight: bool
    adjacent: bool
    thermometers: Sequence[Sequence[Tuple[int, int]]]

    def __init__(self, *, king: bool = False, knight: bool = False, adjacent: bool = False,
                 magic: bool = False,
                 thermometers: Sequence[Sequence[Tuple[int, int]]] = ()) -> None:
        self.king = king
        self.knight = knight
        self.adjacent = adjacent
        self.thermometers = thermometers
        self.magic = magic

    def solve(self, puzzle: str):
        initial_puzzle_grid = {(row, column): int(letter)
                               for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                               if '1' <= letter <= '9'}
        constraints = self.__get_default_constraints()
        optional_constraints = set()
        for (row, column), value in initial_puzzle_grid.items():
            constraints[row, column, value].append(f'Given r{row}c{column}={value}')

        for row, column in itertools.product(range(1, 10), repeat=2):
            if self.knight or self.king:
                neighbors = set()
                if self.knight:
                    neighbors.update(self.knights_move(row, column))
                if self.king:
                    neighbors.update(self.kings_move(row, column))
                # For each "neighbor", we add an optional constraint so that either this cell can have a value or the
                # neighbor can have the value.  This ensures that at most one of them will have the specified value
                for neighbor_row, neighbor_column in neighbors:
                    if (row, column) < (neighbor_row, neighbor_column):
                        for value in range(1, 10):
                            constraint = f'r{row}c{column}={value};r{neighbor_row}c{neighbor_column}={value}'
                            optional_constraints.add(constraint)
                            constraints[row, column, value].append(constraint)
                            constraints[neighbor_row, neighbor_column, value].append(constraint)
            if self.adjacent:
                # For each cell next me me, create an optional constraint such that if I have a specific value,
                # the neighbor cannot also have that value.
                for neighbor_row, neighbor_column in self.adjacent_move(row, column):
                    for value in range(1, 9):  # Note, we don't need to use value=9.
                        constraint = f'r{row}c{column}={value};r{neighbor_row}c{neighbor_column}={value+1}'
                        optional_constraints.add(constraint)
                        constraints[row, column, value].append(constraint)
                        constraints[neighbor_row, neighbor_column, value + 1].append(constraint)

        if self.thermometers:
            # for thermometer in self.thermometers:
            #     for i, (row, column) in enumerate(thermometer, start=1):
            #         constraint = f'r{row}r{column}  Thermometer'
            #         for value in range(i, 10 + i - len(thermometer)):
            #             constraints[row, column, value].append(constraint)
            #     for i, ((row1, column1), (row2, column2)) in enumerate(zip(thermometer, thermometer[1:]), start=1):
            #         for value1 in range(i, 10 + i - len(thermometer)):
            #             for value2 in range(i + 1, 10 + (i + 1) - len(thermometer)):
            #                 if value2 > value1:
            #                     break
            #                 constraint = f'r{row1}c{column1}={value1} < r{row2}c{column2}={value2}'
            #                 optional_constraints.add(constraint)
            #                 constraints[row1, column1, value1].append(constraint)
            #                 constraints[row2, column2, value2].append(constraint)

            for i, thermometer in enumerate(self.thermometers, start=1):
                constraint = f'Thermometer #{i}'
                for values in itertools.combinations(range(1, 10), len(thermometer)):
                    triples = tuple((row, column, value) for (row, column), value in zip(thermometer, values))
                    constraints[triples] = [x for triple in triples for x in constraints[triple]]
                    constraints[triples].append(constraint)
                for row, column in thermometer:
                    for value in range(1, 10):
                        del constraints[row, column, value]

        if self.magic:
            constraints[5, 5, 5].append(f'Given r5c5=5')
            constraint = "Magic Square"
            squares = ((4, 4), (4, 5), (4, 6), (5, 6), (6, 6), (6, 5), (6, 4), (5, 4))
            values = deque((2, 9, 4, 3, 8, 1, 6, 7))
            for _ in range(2):
                for _ in range(4):
                    triples = tuple((row, column, value) for (row, column), value in zip(squares, values))
                    name = ''.join(str(x) for x in values)
                    constraints[name] = [x for triple in triples for x in constraints[triple]]
                    constraints[name].append(constraint)
                    values.rotate(2)
                values.reverse()

            for row, column, value in itertools.product((4, 5, 6), (4, 5, 6), range(1, 10)):
                del constraints[row, column, value]

        links = DancingLinks(constraints, optional_constraints=optional_constraints,
                             row_printer=self.get_grid_printer(initial_puzzle_grid)
                             )
        links.solve(debug=1000, recursive=False)

    def solve_junk(self, puzzle: str) -> None:
        row_triples = [str(x) for x in (0, 423, 273, 137, 625, 216, 815, 162, 742, 324)]
        col_triples = [str(x) for x in (0, 342, 164, 423, 432, 143, 423, 432, 285, 543)]
        optional_constraints = set()
        constraints = self.__get_default_constraints()

        initial_puzzle_grid = {(row, column): int(letter)
                               for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                               if '1' <= letter <= '9'}
        for (row, column), value in initial_puzzle_grid.items():
            constraints[row, column, value].append(f'Required{row}{column}={value}')

        for a in range(1, 10):
            for b, c in itertools.combinations(range(1, 10), 2):
                for index1, index2 in itertools.combinations(range(3), 2):
                    for row1, row2, col1, col2, digit1, digit2 in (
                            (a, a, b, c, int(row_triples[a][index1]), int(row_triples[a][index2])),
                            (b, c, a, a, int(col_triples[a][index1]), int(col_triples[a][index2]))):
                        constraint = f'r{row1}c{col1}={digit2}:r{row2}c{col2}={digit1}'
                        optional_constraints.add(constraint)
                        constraints[row1, col1, digit2].append(constraint)
                        constraints[row2, col2, digit1].append(constraint)

        links = DancingLinks(constraints, optional_constraints=optional_constraints,
                             row_printer=self.get_grid_printer(initial_puzzle_grid))
        links.solve(debug=1000, recursive=False)

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
    def get_grid_printer(initial_puzzle_grid) -> Callable[[Sequence[Tuple[int, int, int]]], None]:
        def draw_grid(results: Sequence[Tuple[int, int, int]]) -> None:
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
                args = given if (row, column) in initial_puzzle_grid else found
                axes.text(column + .5, row + .5, str(value),
                          verticalalignment='center', horizontalalignment='center', **args)
            plt.show()

        return draw_grid

    def __get_default_constraints(self) -> Dict[Tuple[int, int, int], List[str]]:
        def box(row: int, column: int) -> int:
            return row - (row - 1) % 3 + (column - 1) // 3

        return {(row, column, value):
                    [f"V{row}{column}", f"R{row}={value}", f"C{column}={value}", f"B{box(row, column)}={value}"]
                for row, value, column in itertools.product(range(1, 10), repeat=3)
                }


def main() -> None:
    sudoku = Sudoku(thermometers=(
        [(x, 1) for x in range(4, 0, -1)],
        [(x, 1) for x in range(8, 4, -1)],

        [(x, 2) for x in range(4, 0, -1)],
        [(x, 2) for x in range(7, 10)],

        ((1, 4), (2, 4), (2, 3)),
        [(7,3), (7, 4)],

        [(x, 5) for x in range(4, 0, -1)],
        [(x, 5) for x in range(6, 10)],

        [(4, 7), (4, 6)],
        [(7, 6), (8, 6), (8, 7)],

        [(x, 8) for x in range(3, 0, -1)],
        [(x, 8) for x in range(6, 10)],

        [(x, 9) for x in range(2, 6)],
        [(x, 9) for x in range(6, 10)],
    ))
    sudoku.solve('.' * 8)

if __name__ == '__main__':
    main()
