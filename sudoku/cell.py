from enum import Enum, auto
from typing import Sequence, Set, Optional, Iterable, Iterator, NamedTuple, Mapping, Tuple

from color import Color


class House:
    class Type(Enum):
        ROW = auto()
        COLUMN = auto()
        BOX = auto()

        def all_but(self) -> Iterator['House.Type']:
            return (x for x in House.Type if x != self)

    house_type: 'House.Type'
    index: int
    cells: Sequence['Cell']
    unknown_values: Set[int]
    unknown_cells: Set['Cell']

    def __init__(self, house_type: 'House.Type', index: int) -> None:
        self.house_type = house_type
        self.index = index
        self.cells = []
        self.unknown_values = set(range(1, 10))
        self.unknown_cells = set()

    def reset(self) -> None:
        self.unknown_values = set(range(1, 10))
        self.unknown_cells = set(self.cells)

    def __repr__(self) -> str:
        return self.house_type.name.title()[:3] + " " + str(self.index)

    def set_value_to(self, cell: 'Cell', value: int) -> None:
        self.unknown_cells.remove(cell)
        self.unknown_values.remove(value)

    def __lt__(self, other: 'House') -> bool:
        return (self.house_type, self.index) < (other.house_type, other.index)


class Cell:
    houses: Mapping[House.Type, House]
    index: Tuple[int, int]
    known_value: Optional[int]
    possible_values: Set[int]
    neighbors: Set['Cell']

    def __init__(self, row: House, column: House, box: House) -> None:
        self.houses = {House.Type.ROW: row, House.Type.COLUMN: column, House.Type.BOX: box}
        self.index = (row.index, column.index)
        self.known_value = None
        self.possible_values = set(range(1, 10))
        self.neighbors = set()  # Filled in later

    def reset(self) -> None:
        self.known_value = None
        self.possible_values = set(range(1, 10))

    def set_value_to(self, value: int, *, show: bool = False) -> str:
        for house in self.houses.values():
            house.set_value_to(self, value)
        for neighbor in self.neighbors:
            neighbor.possible_values.discard(value)
        assert value in self.possible_values
        self.known_value = value
        self.possible_values.clear()
        self.possible_values.add(value)
        output = f'{self} := {value}'  # Maybe use ⬅
        if show:
            print(f'  {output}')
        return output

    @property
    def is_known(self) -> bool:
        return self.known_value is not None

    def initialize_neighbors(self, all_cells: Iterable['Cell'], *,
                             knight: bool = False, king: bool = False) -> None:
        self.neighbors = {cell for cell in all_cells
                          if cell != self
                          if any(self.houses[type] == cell.houses[type] for type in House.Type)
                             or (knight and self.__is_knights_move(cell))
                             or (king and self.__is_kings_move(cell))
                          }

    def house_of_type(self, house_type: House.Type) -> House:
        return self.houses[house_type]

    def strong_pair(self, house_type: House.Type, value: int) -> Optional['Cell']:
        temp = [cell for cell in self.house_of_type(house_type).unknown_cells
                if cell != self and value in cell.possible_values]
        return temp[0] if len(temp) == 1 else None

    def weak_pair(self, house_type: House.Type, value: int) -> Sequence['Cell']:
        temp = [cell for cell in self.house_of_type(house_type).unknown_cells
                if cell != self and value in cell.possible_values]
        return temp

    def is_neighbor(self, other: 'Cell') -> bool:
        return other in self.neighbors

    def joint_neighbors(self, other: 'Cell') -> Iterator['Cell']:
        return (cell for cell in self.neighbors if other.is_neighbor(cell))

    def __repr__(self) -> str:
        row, column = self.index
        return f"r{row}c{column}"

    def possible_value_string(self) -> str:
        return ''.join(str(i) for i in sorted(self.possible_values))

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other) -> bool:
        return self is other

    def __lt__(self, other: 'Cell') -> bool:
        return (self.index) < (other.index)

    def __is_knights_move(self, other: 'Cell'):
        row1, column1 = self.index
        row2, column2 = other.index
        return {abs(row1 - row2), abs(column1 - column2)} == {1, 2}

    def __is_kings_move(self, other: 'Cell'):
        row1, column1 = self.index
        row2, column2 = other.index
        return max(abs(row1 - row2), abs(column1 - column2)) == 1

    @staticmethod
    def __deleted(i: int):
        return f'{Color.lightgrey}{Color.strikethrough}{i}{Color.reset}'

    @staticmethod
    def remove_value_from_cells(cells: Iterable['Cell'], value: int):
        for cell in cells:
            foo = ''.join((Cell.__deleted(i) if i == value else str(i)) for i in sorted(cell.possible_values))
            cell.possible_values.remove(value)
            print(f'  {cell} = {foo}')

    @staticmethod
    def remove_values_from_cells(cells: Iterable['Cell'], values: Set[int]):
        for cell in cells:
            foo = ''.join((Cell.__deleted(i) if i in values else str(i)) for i in sorted(cell.possible_values))
            cell.possible_values -= values
            print(f'  {cell} = {foo}')


class CellValue(NamedTuple):
    cell: Cell
    value: int

    def __repr__(self) -> str:
        return f'{self.cell}={self.value}'

    def to_string(self, truth: bool):
        char = '=' if truth else '≠'
        return f'{self.cell}{char}{self.value}'
