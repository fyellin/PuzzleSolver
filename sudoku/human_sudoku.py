import itertools
from collections import deque
from operator import attrgetter
from typing import Set, Sequence, Mapping, Iterable

from cell import House, Cell, CellValue
from chain import Chains
from grid import Grid
from hard_medusa import HardMedusa


class Sudoku:
    grid: Grid

    def __init__(self, **args: bool) -> None:
        self.grid = Grid(**args)

    def solve(self, puzzle: str) -> bool:
        grid = self.grid
        grid.reset()
        for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle):
            if '1' <= letter <= '9':
                grid.matrix[row, column].set_value_to(int(letter))
        return self.run_solver()

    def run_solver(self) -> bool:
        while True:
            if self.is_solved():
                return True
            if self.check_naked_singles() or self.check_hidden_singles():
                continue
            if self.check_intersection_removal():
                continue
            if self.check_tuples():
                continue
            self.grid.print()
            if self.check_fish() or self.check_xy_sword() or self.check_xyz_sword() or self.check_tower():
                continue
            if self.check_xy_chain(81):
                continue
            chains = Chains.create(self.grid.cells, True)
            if self.check_chain_colors(chains):
                continue
            if HardMedusa.run(chains):
                continue
            return False

    def is_solved(self) -> bool:
        """Returns true if every square has a known value"""
        return self.grid.is_solved()

    def check_naked_singles(self) -> bool:
        """
        Finds those squares which are forced because they only have one possible remaining value.
        Returns true if any changes are made to the grid
        """
        found_forced_cell = False
        while True:
            # Cells that only have one possible value
            forced_cells = {cell for cell in self.grid.cells
                            if not cell.is_known and len(cell.possible_values) == 1}
            if not forced_cells:
                break
            found_forced_cell = True
            # Officially set the cell to its one possible value
            output = [cell.set_value_to(list(cell.possible_values)[0])
                      for cell in forced_cells]
            print("Forced: " + '; '.join(output))
        return found_forced_cell

    def check_hidden_singles(self) -> bool:
        """
        Finds a house for which there is only one place that one or more digits can go.
        Returns true if it finds such a house.
        """
        return any(self.__check_hidden_singles(house) for house in self.grid.houses)

    @staticmethod
    def __check_hidden_singles(house: House) -> bool:
        # Make a sorted list of all cell/value combinations not yet known
        all_unknown_cell_values = [CellValue(cell, value)
                                   for cell in house.unknown_cells
                                   for value in cell.possible_values]
        all_unknown_cell_values.sort(key=attrgetter("value"))
        result = False
        for value, iterator in itertools.groupby(all_unknown_cell_values, attrgetter("value")):
            cell_values = tuple(iterator)
            if len(cell_values) == 1:
                cell = cell_values[0].cell
                cell.set_value_to(value)
                print(f'Hidden Single: {house} = {value} must be {cell}')
                result = True
        return result

    def check_intersection_removal(self) -> bool:
        """
        Original explanation:
        If the only possible places to place a digit in a particular house are all also within another house, then
        all other occurrences of that digit in the latter house can be deleted.

        New explanation:
        If the only possible places to place a digit in a particular house are all neighbors of a cell outside the
        house, then that outside cell cannot contain the digit (or it would eliminate all the possibilities.)  This
        is more general than the original explanation, and allows this to work with knight- and king-sudoku, too.

        Returns true if we make a change.
        """
        return any(self.__check_intersection_removal(house, value)
                   for house in self.grid.houses
                   for value in house.unknown_values)

    @staticmethod
    def __check_intersection_removal(house: House, value: int) -> bool:
        """Checks for intersection removing of the specific value in the specific house"""
        candidates = [cell for cell in house.unknown_cells if value in cell.possible_values]
        assert len(candidates) > 1
        cell0, *other_candidates = candidates
        # Find all cells that both have the specified value, and are neighbors of all the candidates.
        fixers = {cell for cell in cell0.neighbors if value in cell.possible_values}
        fixers.intersection_update(*(cell.neighbors for cell in other_candidates))
        if fixers:
            print(f'Intersection Removal: {house} = {value} must be one of {sorted(candidates)}')
            Cell.remove_value_from_cells(fixers, value)
            return True
        return False

    def check_tuples(self) -> bool:
        """
        If there are a group of n cells, all of whose possible values are a subset of a specific n digits, then
        that digit can only occur in one of those n cells.
        Returns true if it makes any change.
        """
        return any(self.__check_tuples(house, set(values))
                   # Specifically find all tuples of 2 before trying all tuples of 3, . . . .
                   for count in range(2, 9)
                   # Look at each house
                   for house in self.grid.houses if len(house.unknown_values) > count
                   # Look at each subset of size "count" of the unknown values of that house
                   for values in itertools.combinations(house.unknown_values, count))

    @staticmethod
    def __check_tuples(house: House, values: Set[int]):
        """
        Looks to see if "values" is a tuple in this house.  Returns true if it makes any changes.
        """
        # Find those cells in this house whose possible values are a subset of the tuple
        tuple_cells = [cell for cell in house.unknown_cells if cell.possible_values <= values]
        if len(tuple_cells) != len(values):
            return False
        # We have precisely the right number.  Delete these values if they occur in any other cells
        fixers = [cell for cell in house.unknown_cells
                  if cell not in tuple_cells and cell.possible_values & values]
        if not fixers:
            return False

        # Let n = len(values) and k = len(house.unknown_values) - n
        # We've discovered that n cells only contain a subset of n values.  But that means that the remaining
        # k values only occur in the remaining k cells.  Both same the same thing.   We can look at what we're about
        # to do as either
        #     (1) The n values can only occur in those n cells, and must be deleted from all other cells or
        #     (2) The remaining k values must occur in those k cells, and all other digits can be deleted.
        # Both say the same thing.  How we word it depends on which is smaller, n or k.
        if len(values) * 2 <= len(house.unknown_values):
            print(f'{house} has tuple {sorted(values)} in squares {sorted(tuple_cells)}:')
        else:
            hidden_tuple = house.unknown_values - values
            hidden_squares = house.unknown_cells.difference(tuple_cells)
            print(f'{house} has hidden tuple {sorted(hidden_tuple)} in squares {sorted(hidden_squares)}:')
        Cell.remove_values_from_cells(fixers, values)
        return True

    def check_fish(self) -> bool:
        """Looks for a fish of any size.  Returns true if a change is made to the grid."""
        for value in range(1, 10):
            # Find all houses for which the value is missing
            empty_houses = [house for house in self.grid.houses if value in house.unknown_values]
            if not empty_houses:
                continue
            # For convenience, make a map from each "empty" house to the cells in that house that can contain the value
            empty_house_to_cell = {house: [cell for cell in house.unknown_cells if value in cell.possible_values]
                                   for house in empty_houses}
            # Look for a fish between any two House types on the specified value
            # noinspection PyTypeChecker
            for this_house_type, that_house_type in itertools.permutations(House.Type, 2):
                if self.__check_fish(value, empty_houses, empty_house_to_cell, this_house_type, that_house_type):
                    return True
        return False

    @staticmethod
    def __check_fish(value: int,
                     empty_houses: Sequence[House],
                     empty_house_to_cell: Mapping[House, Sequence[Cell]],
                     this_house_type: House.Type,
                     that_house_type: House.Type) -> bool:
        these_unknown_houses = [house for house in empty_houses if house.house_type == this_house_type]
        those_unknown_houses = [house for house in empty_houses if house.house_type == that_house_type]
        assert len(these_unknown_houses) == len(those_unknown_houses) >= 2
        unknown_size = len(these_unknown_houses)
        # We arbitrarily pretend that this_house_type is ROW and that_house_type is COLUMN in the naming of our
        # variables below.  But that's just to simplify the algorithm.  Either House can be any time.
        max_rows_to_choose = unknown_size - 1
        if this_house_type == House.Type.BOX or that_house_type == House.Type.BOX:
            max_rows_to_choose = min(2, max_rows_to_choose)
        # Look at all subsets of the rows, but do small subsets before doing large subsets
        for number_rows_to_choose in range(2, max_rows_to_choose + 1):
            for rows in itertools.combinations(these_unknown_houses, number_rows_to_choose):
                # Find all the possible cells in those rows
                row_cells = {cell for house in rows for cell in empty_house_to_cell[house]}
                # Find the columns that those cells belong to
                columns = {cell.house_of_type(that_house_type) for cell in row_cells}
                assert len(columns) >= number_rows_to_choose
                if len(columns) > number_rows_to_choose:
                    continue
                # If len(columns) == number_rows_to_choose, we have a fish.  Let's see if there is something to delete.
                # Find all the cells in those columns
                column_cells = {cell for house in columns for cell in empty_house_to_cell[house]}
                assert row_cells <= column_cells
                if len(row_cells) < len(column_cells):
                    # There are some column cells that aren't in our rows.  The value can be deleted.
                    fixer_cells = column_cells - row_cells
                    print(f'Fish.  { tuple(sorted(columns))} must have {value} only on {tuple(sorted(rows)) }')
                    Cell.remove_value_from_cells(fixer_cells, value)
                    return True
        return False

    def check_xy_sword(self) -> bool:
        return self.check_xy_chain(3)

    def check_xy_chain(self, max_length: int = 81) -> bool:
        """
        Look at every cell and see if we can create an xy-chain. up to the specified length.
        Returns true if a change is made to the grid.

        An XY chain is a chain of cells, each of which is a cell with two possible values, and in which each cell
        is  neighbor of the previous one and has a digit in common with the previous one.  Given a chain
        AB - BC - CA (a sword), we know that either the first element or the last element must be an A.  Hence any
        cell visible to both of them can't contain A.
        """
        return any(self.__check_xy_chain(cell, value, max_length)
                   for cell in self.grid.cells
                   if len(cell.possible_values) == 2
                   for value in cell.possible_values)

    @staticmethod
    def __check_xy_chain(init_cell: Cell, init_value: int, max_length: int):
        todo = deque([(init_cell, init_value, 1)])
        links = {(init_cell, init_value): ((init_cell, init_value), 0)}

        def run_queue() -> bool:
            while todo:
                cell, value, depth = todo.popleft()
                next_value = (cell.possible_values - {value}).pop()
                for next_cell in cell.neighbors:
                    if len(next_cell.possible_values) == 2 and next_value in next_cell.possible_values:
                        if not (next_cell, next_value) in links:
                            new_depth = depth + 1
                            if new_depth < max_length:
                                todo.append((next_cell, next_value, depth + 1))
                            links[(next_cell, next_value)] = ((cell, value), depth + 1)
                            if look_for_cell_to_update(next_cell, next_value, depth + 1):
                                return True
            return False

        def look_for_cell_to_update(next_cell: Cell, next_value: int, depth: int) -> bool:
            if depth >= 3 and init_cell != next_cell and init_cell not in next_cell.neighbors:
                if init_value != next_value and init_value in next_cell.possible_values:
                    # We can remove init_value from any cell that sees both init_cell and next_cell
                    fixers = {cell for cell in init_cell.joint_neighbors(next_cell)
                              if init_value in cell.possible_values}
                    if fixers:
                        print(f'Found an XY chain {chain_to_string(next_cell, next_value)}')
                        Cell.remove_value_from_cells(fixers, init_value)
                        return True
            return False

        def chain_to_string(next_cell: Cell, next_value: int) -> str:
            result = [str(init_value)]
            cell, value = next_cell, next_value
            while True:
                result.append(f'{cell}={cell.possible_value_string()}')
                (cell, value), depth = links[cell, value]
                if depth == 0:
                    return ' '.join(result)

        run_queue()

    def check_xyz_sword(self) -> bool:
        for triple in self.grid.cells:
            if len(triple.possible_values) == 3:
                possibilities = [cell for cell in triple.neighbors
                                 if len(cell.possible_values) == 2 and cell.possible_values <= triple.possible_values]
                for pair1, pair2 in itertools.combinations(possibilities, 2):
                    if pair1.possible_values != pair2.possible_values:
                        common = pair1.possible_values.intersection(pair2.possible_values).pop()
                        fixers = [cell for cell in pair1.joint_neighbors(pair2)
                                  if cell.is_neighbor(triple) and common in cell.possible_values]
                        if fixers:
                            print(
                                f'Found XYZ sword {pair1}={pair1.possible_value_string()}, '
                                f'{pair2}={pair2.possible_value_string()}, '
                                f'{triple}={triple.possible_value_string()}')
                            Cell.remove_value_from_cells(fixers, common)
                            return True
        return False

    @staticmethod
    def check_chain_colors(chains: Chains) -> bool:
        """
        Create strong chains for all the unsolved cells.  See if looking at any two items on the same chain
        yields an insight or contradiction.
        """
        return any(chain.check_colors() for chain in chains.chains)

    def check_tower(self) -> bool:
        def strong_pair_iterator(cell: Cell, house_type: House.Type, val: int) -> Iterable[Cell]:
            paired_cell = cell.strong_pair(house_type, val)
            if paired_cell:
                yield paired_cell

        for cell1 in self.grid.cells:
            if cell1.is_known:
                continue
            for value in cell1.possible_values:
                for house_type1 in House.Type:
                    for cell2 in strong_pair_iterator(cell1, house_type1, value):
                        for house_type2 in house_type1.all_but():
                            for cell3 in cell2.weak_pair(house_type2, value):
                                for house_type3 in house_type2.all_but():
                                    for cell4 in strong_pair_iterator(cell3, house_type3, value):
                                        if cell4 in (cell1, cell2, cell3):
                                            continue
                                        fixers = {cell for cell in cell1.joint_neighbors(cell4)
                                                  if value in cell.possible_values}
                                        if fixers:
                                            print(f'Tower on /{value}/ {cell1}={cell2}-{cell3}={cell4}')
                                            Cell.remove_value_from_cells(fixers, value)
                                            return True
        return False


def main() -> None:
    unsolved = []
    sudoku = Sudoku(knight=True)
    PUZZLES = [
        '.....5...'
        '1......7.'
        '........2'
        '6.4..7...'
        '...8...6.'
        '.........'
        '...2.....'
        '...39....'
        '.........'
    ]
    for i, puzzle in enumerate(PUZZLES):
        assert len(puzzle) == 81
        print()
        print('--------------------')
        print()
        print(i, puzzle)
        try:
            result = sudoku.solve(puzzle)
        except Exception:
            print(puzzle)
            raise

        if not result:
            unsolved.append(puzzle)
    for puzzle in unsolved:
        print(puzzle)
    print(f"Failed to solve {len(unsolved)} puzzles")


if __name__ == '__main__':
    main()


