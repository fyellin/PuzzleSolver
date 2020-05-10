from enum import Enum, auto
from typing import Sequence, Set, Optional, Iterable, Iterator, NamedTuple


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

    def __init__(self, type: 'House.Type', index: int) -> None:
        self.house_type = type
        self.index = index
        self.cells = []
        self.unknown_values = set(range(1, 10))
        self.unknown_cells = set()

    def __str__(self) -> str:
        return self.house_type.name.title() + " " + str(self.index)

    def __repr__(self) -> str:
        return str(self)

    def set_value_to(self, cell: 'Cell', value: int) -> None:
        self.unknown_cells.remove(cell)
        self.unknown_values.remove(value)

    def __lt__(self, other: 'House') -> bool:
        return (self.house_type, self.index) < (other.house_type, other.index)


class Cell:
    row: House
    column: House
    box: House
    known_value: Optional[int]
    possible_values: Set[int]
    neighbors: Set['Cell']

    def __init__(self, row: House, column: House, box: House) -> None:
        self.row = row
        self.column = column
        self.box = box
        self.known_value = None
        self.possible_values = set(range(1, 10))
        self.neighbors = set()  # Filled in later

    def set_value_to(self, value: int) -> None:
        for house in (self.row, self.column, self.box):
            house.set_value_to(self, value)
        for neighbor in self.neighbors:
            neighbor.possible_values.discard(value)
        assert value in self.possible_values
        self.known_value = value
        self.possible_values.clear()
        self.possible_values.add(value)

    @property
    def is_known(self) -> bool:
        return self.known_value is not None

    def initialize_neighbors(self, all_cells: Iterable['Cell']) -> None:
        neighbors = {cell for cell in all_cells
                     if cell != self
                     if self.row == cell.row or self.column == cell.column or self.box == cell.box}
        self.neighbors = neighbors

    def get_common_house(self, other: 'Cell') -> House:
        if self.row == other.row:
            return self.row
        if self.column == other.column:
            return self.column
        if self.box == other.box:
            return self.box
        assert False

    def house_of_type(self, house_type: House.Type) -> House:
        if house_type == House.Type.BOX:
            return self.box
        if house_type == House.Type.COLUMN:
            return self.column
        if house_type == House.Type.ROW:
            return self.row
        assert False

    def strong_pair(self, house_type: House.Type, value: int) -> Optional['Cell']:
        temp = [cell for cell in self.house_of_type(house_type).unknown_cells if cell != self and value in cell.possible_values]
        return temp[0] if len(temp) == 1 else None

    def weak_pair(self, house_type: House.Type, value: int) -> Sequence['Cell']:
        temp = [cell for cell in self.house_of_type(house_type).unknown_cells if cell != self and value in cell.possible_values]
        return temp

    def is_neighbor(self, other: 'Cell') -> bool:
        return other in self.neighbors

    def joint_neighbors(self, other: 'Cell') -> Iterator['Cell']:
        return (cell for cell in self.neighbors if other.is_neighbor(cell))


    def __str__(self) -> str:
        return f"r{self.row.index}c{self.column.index}"

    def __repr__(self) -> str:
        return str(self)

    def possible_value_string(self) -> str:
        return ''.join(str(i) for i in sorted(self.possible_values))

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other) -> bool:
        return isinstance(other, Cell) and self.row.index == other.row.index and self.column.index == other.column.index

    def __lt__(self, other: 'Cell') -> bool:
        return (self.row.index, self.column.index) < (other.row.index, other.column.index)


class CellValue(NamedTuple):
    cell: Cell
    value: int

    def __str__(self) -> str:
        return f'{self.cell}={self.value}'

