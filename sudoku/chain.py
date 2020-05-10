from collections import deque
from enum import Enum, auto
from typing import Set, Iterable, Tuple, Iterator

from cell import CellValue, Cell, House


class Chain:
    one: Set[CellValue]
    two: Set[CellValue]

    class Group (Enum):
        ONE = auto()
        TWO = auto()

        def pick_set(self, chain: 'Chain') -> Set[CellValue]:
            return chain.one if self == Chain.Group.ONE else chain.two

        def pick_other_set(self, chain: 'Chain') -> Set[CellValue]:
            return chain.two if self == Chain.Group.ONE else chain.one

        def other(self) -> 'Chain.Group':
            return Chain.Group.ONE if self == Chain.Group.TWO else Chain.Group.TWO


    def __init__(self) -> None:
        self.one = set()
        self.two = set()

    @staticmethod
    def create(start: CellValue, medusa: bool) -> 'Chain':
        chain = Chain()
        todo = deque([(start, 0)])
        seen = {start}
        while todo:
            cell_value, depth = todo.popleft()
            (chain.one if depth % 2 == 0 else chain.two).add(cell_value)
            (this_cell, this_value) = cell_value
            for house_type in House.Type:
                next_cell = this_cell.strong_pair(house_type, this_value)
                if next_cell is None:
                    continue
                next_cell_value = CellValue(next_cell, this_value)
                if next_cell_value not in seen:
                    seen.add(next_cell_value)
                    todo.append((next_cell_value, depth + 1))
            if medusa and len(this_cell.possible_values) == 2:
                next_value = (this_cell.possible_values - {this_value}).pop()
                next_cell_value = CellValue(this_cell, next_value)
                if next_cell_value not in seen:
                    seen.add(next_cell_value)
                    todo.append((next_cell_value, depth + 1))
        return chain

    @staticmethod
    def get_all_chains(all_cells: Iterable[Cell], medusa: bool):
        seen: Set[CellValue] = set()
        chains = []
        for cell in all_cells:
            if cell.is_known:
                continue
            for value in cell.possible_values:
                cell_value = CellValue(cell, value)
                if cell_value not in seen:
                    chain = Chain.create(cell_value, medusa)
                    chains.append(chain)
                    seen.update(chain.one)
                    seen.update(chain.two)
        chains.sort(reverse=True)
        return chains

    def set_true(self, group: 'Chain.Group') -> None:
        print(f"Setting value of {self} to  " + ("A" if group == Chain.Group.ONE else 'a'))
        for cell, value in group.pick_other_set(self):
            cell.possible_values.discard(value)
            print(f'  {cell} ≠ {value} ∈ {cell.possible_value_string()}')
        for cell, value in group.pick_set(self):
            cell.set_value_to(value)
            print(f'  {cell} := {value}')

    def get_group(self, cell_value: CellValue) -> 'Chain.Group':
        if cell_value in self.one:
            return Chain.Group.ONE
        if cell_value in self.two:
            return Chain.Group.TWO
        assert False

    def items(self) -> Iterator[Tuple[CellValue, 'Chain.Group']]:
        yield from ((cell, Chain.Group.ONE) for cell in self.one)
        yield from ((cell, Chain.Group.TWO) for cell in self.two)

    def to_string(self, group: 'Chain.Group') -> str:
        items: Set[Tuple[CellValue, str]] = set()
        items.update((cv, '=') for cv in group.pick_set(self))
        items.update((cv, '≠') for cv in group.pick_other_set(self))
        return ', '.join(f'{cell}{symbol}{value}' for (cell, value), symbol in sorted(items))

    def __repr__(self) -> str:
        items: Set[Tuple[CellValue, str]] = set()
        items.update((cv, 'A') for cv in self.one)
        items.update((cv, 'a') for cv in self.two)
        return ', '.join(f'{cell}={value}({symbol})' for (cell, value), symbol in sorted(items))

    def __len__(self) -> int:
        return len(self.one) + len(self.two)

    def __lt__(self, other: 'Chain') -> bool:
        return len(self) < len(other)
