import datetime
import itertools
from typing import Tuple, Sequence, Callable, Dict, List

from matplotlib import pyplot as plt

from solver import DancingLinks


class Sudoku:
    king: bool
    knight: bool
    adjacent: bool

    def __init__(self, *, king: bool = False, knight: bool = False, adjacent: bool = False) -> None:
        self.king = king
        self.knight = knight
        self.adjacent = adjacent

    def solve(self, puzzle: str):
        initial_puzzle_grid = {(row, column): int(letter)
                               for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                               if '1' <= letter <= '9'}
        constraints = self.__get_default_constraints()
        optional_constraints = set()
        for (row, column), value in initial_puzzle_grid.items():
            constraints[row, column, value].append(f'Required{row}{column}={value}')

        for row, column in itertools.product(range(1, 10), repeat=2):
            if self.knight or self.king:
                neighbors = set()
                if self.knight:
                    neighbors.update(self.knights_move(row, column))
                if self.king:
                    neighbors.update(self.kings_move(row, column))
                for neighbor_row, neighbor_column in neighbors:
                    if (row, column) < (neighbor_row, neighbor_column):
                        for value in range(1, 10):
                            constraint = f'r{row}c{column}={value};r{neighbor_row}c{neighbor_column}={value}'
                            optional_constraints.add(constraint)
                            constraints[row, column, value].append(constraint)
                            constraints[neighbor_row, neighbor_column, value].append(constraint)
            if self.adjacent:
                for neighbor_row, neighbor_column in self.adjacent_move(row, column):
                    for value in range(1, 9):  # Note, we don't need to use value=9.
                        constraint = f'r{row}c{column}={value};r{neighbor_row}c{neighbor_column}={value+1}'
                        optional_constraints.add(constraint)
                        constraints[row, column, value].append(constraint)
                        constraints[neighbor_row, neighbor_column, value + 1].append(constraint)

        links = DancingLinks(constraints, optional_constraints=optional_constraints,
                             row_printer=self.get_grid_printer(initial_puzzle_grid)
                             )
        links.solve(debug=1000, recursive=False)

    def solve_junk(self) -> None:
        row_triples = [str(x) for x in (0, 423, 273, 137, 625, 216, 815, 162, 742, 324)]
        col_triples = [str(x) for x in (0, 342, 164, 423, 432, 143, 423, 432, 285, 543)]
        optional_constraints = set()

        constraints = self.__get_default_constraints()
        constraints[3, 8, 7].append("Required387")

        for a in range(1, 10):
            for b, c in itertools.combinations(range(1, 10), 2):
                for index1, index2 in itertools.combinations(range(3), 2):
                    row1, row2, col1, col2 = a, a, b, c
                    digit1, digit2 = int(row_triples[row1][index1]), int(row_triples[row2][index2])
                    constraint = f'r{row1}c{col1}:r{row2}c{col2}:{digit1}<{digit2}'
                    optional_constraints.add(constraint)
                    constraints[row1, col1, digit2].append(constraint)
                    constraints[row1, col2, digit1].append(constraint)

                    col1, col2, row1, row2 = a, a, b, c
                    digit1, digit2 = int(col_triples[col1][index1]), int(col_triples[col2][index2])
                    constraint = f'r{row1}c{col1}:r{row2}c{col2}:{digit1}<{digit2}'
                    optional_constraints.add(constraint)
                    constraints[row1, col1, digit2].append(constraint)
                    constraints[row2, col2, digit1].append(constraint)

        links = DancingLinks(constraints, optional_constraints=optional_constraints,
                             row_printer=self.get_grid_printer({}))
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
                [f"Value{row}{column}", f"Row{row}={value}", f"Col{column}={value}",
                     f"Box{box(row, column)}={value}"]
                for row, value, column in itertools.product(range(1, 10), repeat=3)
               }




def main() -> None:
    puzzles = [
        '.........'
        '.........'
        '.........'
        '.........'
        '..1......'
        '......2..'
        '.........'
        '.........'
        '.........'
        ]
    start = datetime.datetime.now()
    Sudoku(knight=True, king=True, adjacent=True).solve(puzzles[0])
    end = datetime.datetime.now()
    print(end - start)


if __name__ == '__main__':
    main()
