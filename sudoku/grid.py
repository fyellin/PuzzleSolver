from typing import Dict, Tuple, Sequence, Iterable

from cell import Cell, House


class Grid:
    matrix: Dict[Tuple[int, int], Cell]
    houses: Sequence[House]

    def __init__(self) -> None:
        row_houses = [House(House.Type.ROW, index) for index in range(1, 10)]
        column_houses = [House(House.Type.COLUMN, index) for index in range(1, 10)]
        box_houses = [House(House.Type.BOX, index) for index in range(1, 10)]
        all_houses = tuple(row_houses + column_houses + box_houses)
        all_cells = {}

        for row in range(1, 10):
            for column in range(1, 10):
                row_house = row_houses[row - 1]
                column_house = column_houses[column - 1]
                box = row - (row - 1) % 3 + (column - 1) // 3
                box_house = box_houses[box - 1]
                cell = Cell(row_house, column_house, box_house)
                all_cells[(row, column)] = cell
                for house in (row_house, column_house, box_house):
                    house.unknown_cells.add(cell)

        for house in all_houses:
            house.cells = tuple(sorted(house.unknown_cells))

        for cell in all_cells.values():
            cell.initialize_neighbors(all_cells.values())

        self.matrix = all_cells
        self.houses = all_houses

    def reset(self) -> None:
        for house in self.houses:
            house.reset()
        for cell in self.cells:
            cell.reset()

    def is_solved(self) -> bool:
        return all(cell.is_known for cell in self.cells)

    @property
    def cells(self) -> Iterable[Cell]:
        return self.matrix.values()

    def print(self, marks: bool = True) -> None:
        import sys
        out = sys.stdout
        matrix = self.matrix
        max_length = max(len(cell.possible_values) for cell in self.cells)
        is_solved = max_length == 1
        max_length = 1 if is_solved or not marks else max(max_length, 3)
        for row in range(1, 10):
            for column in range(1, 10):
                cell = matrix[row, column]
                if max_length == 1:
                    if cell.is_known:
                        out.write(f'{cell.known_value}')
                    else:
                        out.write('*')
                elif cell.is_known:
                    string = f'*{cell.known_value}*'
                    out.write(string.center(max_length, ' '))
                else:
                    string = ''.join(str(i) for i in sorted(cell.possible_values))
                    out.write(string.center(max_length, ' '))
                out.write(' | ' if column == 3 or column == 6 else ' ')
            out.write('\n')
            if row == 3 or row == 6:
                out.write('-' * (3 * max_length + 2))
                out.write('-+-')
                out.write('-' * (3 * max_length + 2))
                out.write('-+-')
                out.write('-' * (3 * max_length + 2))
                out.write('\n')
