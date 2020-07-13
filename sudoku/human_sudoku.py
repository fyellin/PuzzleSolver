from __future__ import annotations

import itertools
from collections import deque, defaultdict
from operator import attrgetter
from typing import Set, Sequence, Mapping, Iterable, Tuple, Optional, List, Any

import matplotlib.pyplot as plt

from cell import House, Cell, CellValue
from chain import Chains
from grid import Grid
from hard_medusa import HardMedusa


class Sudoku:
    grid: Grid
    features: Sequence[Feature]
    initial_grid: Mapping[Tuple[int, int], int]

    def solve(self, puzzle: str, *, features: Sequence[Feature] = (), **args: bool) -> bool:
        self.grid = grid = Grid(**args)
        self.features = features
        grid.reset()
        self.initial_grid = {(row, column): int(letter)
                             for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                             if '1' <= letter <= '9'}

        for square, value in self.initial_grid.items():
            grid.matrix[square].set_value_to(value)
        return self.run_solver()

    def run_solver(self) -> bool:
        self.grid.print()

        for feature in self.features:
            feature.initialize(self)

        self.draw_grid()

        while True:
            if self.is_solved():
                return True
            if self.check_naked_singles() or self.check_hidden_singles():
                continue
            if any(feature.check(self) for feature in self.features):
                continue
            if self.check_intersection_removal():
                continue
            if self.check_tuples():
                continue
            if any(feature.extra_check(self) for feature in self.features):
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
        found_naked_single = False
        while True:
            # Cells that only have one possible value
            naked_singles = {cell for cell in self.grid.cells
                             if not cell.is_known and len(cell.possible_values) == 1}
            if not naked_singles:
                break
            found_naked_single = True
            # Officially set the cell to its one possible value
            output = [cell.set_value_to(list(cell.possible_values)[0])
                      for cell in naked_singles]
            print("Naked single: " + '; '.join(output))
        return found_naked_single

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

    def draw_grid(self) -> None:
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

        for feature in self.features:
            feature.draw(self)

        given = dict(fontsize=13, color='black', weight='heavy')
        found = dict(fontsize=12, color='blue', weight='normal')
        for cell in self.grid.cells:
            row, column = cell.index
            if cell.known_value:
                args = given if cell.index in self.initial_grid else found
                axes.text(column + .5, row + .5, cell.known_value,
                          verticalalignment='center', horizontalalignment='center', **args)
            else:
                axes.text(column + .5, row + .5, cell.possible_value_string(),
                          verticalalignment='center', horizontalalignment='center',
                          fontsize=8, color='red', weight='light')

        plt.show()


class Feature:
    def initialize(self, sudoku: Sudoku):
        pass

    def check(self, sudoku: Sudoku) -> bool: ...

    def extra_check(self, sudoku: Sudoku) -> bool:
        return False

    def draw(self, sudoku: Sudoku) -> None:
        pass

    @staticmethod
    def draw_line(points: Sequence[Tuple[int, int]], *, closed: bool = False, **kwargs: Any) -> None:
        ys = [row + .5 for row, _ in points]
        xs = [column + .5 for _, column in points]
        if closed:
            ys.append(ys[0])
            xs.append(xs[0])
        plt.plot(xs, ys, **{'color': 'black', **kwargs})


class MagicSquareFeature(Feature):
    squares: Sequence[Tuple[int, int]]

    def __init__(self, squares:  Sequence[Tuple[int, int]]):
        assert len(squares) == 9
        self.squares = squares

    def check(self, sudoku: Sudoku) -> bool:
        cells = [sudoku.grid.matrix[location] for location in self.squares]
        if not cells[4].is_known:
            print(f'Initial magic square')
            cells[4].set_value_to(5, show=True)
            Cell.remove_values_from_cells((cells[0], cells[2], cells[6], cells[8]), {1, 3, 5, 7, 9})
            Cell.remove_values_from_cells((cells[1], cells[3], cells[5], cells[7]), {2, 4, 5, 6, 8})
            return True

        for temp in ((0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)):
            row = [cells[i] for i in temp]
            legal_triples = [triple for triple in itertools.product(*(x.possible_values for x in row))
                             if sum(triple) == 15]
            actual_possible_values = [{triple[i] for triple in legal_triples} for i in range(3)]
            expected_possible_values = [cell.possible_values for cell in row]
            if actual_possible_values != expected_possible_values:
                print(f'{" + ".join(map(str, row))} = 15')
                for cell, expected, actual in zip(row, expected_possible_values, actual_possible_values):
                    assert actual <= expected
                    if len(actual) < len(expected):
                        Cell.remove_values_from_cells([cell], expected - actual)
                return True
        return False


class GermanSnakeFeature(Feature):
    GERMAN_SNAKE_INFO = {1: {6, 7, 8, 9}, 2: {7, 8, 9}, 3: {8, 9}, 4: {9},
                         6: {1}, 7: {1, 2}, 8: {1, 2, 3}, 9: {1, 2, 3, 4}}

    snake: Sequence[Tuple[int, int]]
    snake_cells: Sequence[Cell]

    def __init__(self, snake:  Sequence[Tuple[int, int]]):
        self.snake = snake

    def initialize(self, sudoku: Sudoku):
        self.snake_cells = [sudoku.grid.matrix[location] for location in self.snake]
        print("No Fives in a German Snake")
        fives = [cell for cell in self.snake_cells if 5 in cell.possible_values]
        Cell.remove_value_from_cells(fives, 5)

    def check(self, sudoku: Sudoku) -> bool:
        previous_cells = itertools.chain([None], self.snake_cells)
        next_cells = itertools.chain(itertools.islice(self.snake_cells, 1, None), itertools.repeat(None))

        for cell, previous, next in zip(self.snake_cells, previous_cells, next_cells):
            impossible_values = set()
            for value in cell.possible_values:
                prev_bridge = self.get_bridge(cell, previous, value)
                next_bridge = self.get_bridge(cell, next, value)
                if not prev_bridge or not next_bridge:
                    impossible_values.add(value)
                elif previous and next and previous.is_neighbor(next) and len(prev_bridge.union(next_bridge)) == 1:
                    impossible_values.add(value)

            if impossible_values:
                print("No appropriate value in adjacent cell")
                Cell.remove_values_from_cells([cell], impossible_values)
                return True
        return False

    def draw(self, _sudoku: Sudoku) -> None:
        xs = [column + .5 for _, column in self.snake]
        ys = [row + .5 for row, _ in self.snake]
        plt.plot(xs, ys, color='gold', linewidth=5)

    def get_bridge(self, cell: Optional[Cell], adjacent: Cell, value: int):
        good_adjacent_values = self.GERMAN_SNAKE_INFO[value]
        if not adjacent:
            return good_adjacent_values
        bridge = adjacent.possible_values.intersection(good_adjacent_values)
        if cell.is_neighbor(adjacent) and value in bridge:
            bridge.discard(value)
        return bridge



class MalvoloRingFeature(Feature):
    MARVOLO_RING_INFO = {1: (3, 7, 8), 2: {2, 6, 7}, 3: {1, 5, 6}, 4: {4, 5}, 5: {3, 4}, 6: {2, 3}, 7: {1, 2, 9},
                         8: {1, 8}, 9: {7}}
    ring_cells: Sequence[Cell]

    def initialize(self, sudoku: Sudoku):
        self.ring_cells = [sudoku.grid.matrix[x] for x in (
            (2, 4), (2, 5), (2, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 7),
            (8, 6), (8, 5), (8, 4), (7, 3), (6, 2), (5, 2), (4, 2), (3, 3))]

    def check(self, sudoku: Sudoku) -> bool:
        for index, cell in enumerate(self.ring_cells):
            impossible_values = set()
            for value in cell.possible_values:
                adjacent1, adjacent2 = (self.ring_cells[(index - 1) % 16], self.ring_cells[(index + 1) % 16])
                bridge1, bridge2 = self.get_bridge(cell, adjacent1, value), self.get_bridge(cell, adjacent2, value)
                if not bridge1 or not bridge2:
                    impossible_values.add(value)
                elif adjacent1.is_neighbor(adjacent2) and len(bridge1.union(bridge2)) == 1:
                    # You can't use the same value on both sides if it is a neighbor to both
                    impossible_values.add(value)

            if impossible_values:
                print("No appropriate value in adjacent cells")
                Cell.remove_values_from_cells([cell], impossible_values)
                return True

        items = defaultdict(list)
        for cell in self.ring_cells:
            for value in cell.possible_values:
                items[value].append(cell)
        for value in range(1, 10):
            if len(items[value]) == 1:
                cell = items[value].pop()
                if len(cell.possible_values) > 1:
                    print(f'Ring:  Value {value} must be {cell}')
                    cell.set_value_to(value)
                    return True

        return False

    def extra_check(self, sudoku: Sudoku) -> bool:
        sudoku.draw_grid()
        temp = sudoku.grid.matrix[2, 6]
        if len(temp.possible_values) == 2:
            print("Danger, danger")
            Cell.remove_value_from_cells([temp], 4)
            return True
        return False

    def draw(self, _sudoku: Sudoku) -> None:
        plt.gca().add_patch(plt.Circle((5.5, 5.5), radius=3, fill=False, facecolor='black'))

    def get_bridge(self, cell: Cell, adjacent: Cell, value: int):
        good_adjacent_values = self.MARVOLO_RING_INFO[value]
        bridge = adjacent.possible_values.intersection(good_adjacent_values)
        if cell.is_neighbor(adjacent) and value in bridge:
            bridge.discard(value)
        return bridge


class SnakeFeature(Feature):
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def initialize(self, sudoku: Sudoku):
        self.cells = [sudoku.grid.matrix[square] for square in self.squares]

    def check(self, sudoku: Sudoku) -> bool:
        known_values = {cell.known_value for cell in self.cells if cell.is_known}
        need_pruning = [cell for cell in self.cells
                        if not cell.is_known and cell.possible_values.intersection(known_values)]
        if need_pruning:
            print("Removing duplicate values from crown")
            Cell.remove_values_from_cells(need_pruning, known_values)
            return True

        items = defaultdict(list)
        for cell in self.cells:
            for value in cell.possible_values:
                items[value].append(cell)
        for value in range(1, 10):
            if len(items[value]) == 1:
                cell = items[value].pop()
                if len(cell.possible_values) > 1:
                    print(f'Ring:  Value {value} must be {cell}')
                    cell.set_value_to(value)
                    return True

        return False

    def draw(self, sudoku: Sudoku) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))



class ContainsTextFeature(Feature):
    spans: List[List[Tuple[int, Cell]]]
    text: Sequence[int]
    row: int
    done: bool

    def __init__(self, row: int, text: Sequence[int]) -> None:
        super().__init__()
        self.row = row
        self.text = text

    def initialize(self, sudoku: Sudoku) -> None:
        cells = [sudoku.grid.matrix[self.row, column] for column in range(1, 10)]
        self.spans = [list(zip(self.text, cells[i:])) for i in range(10 - len(self.text))]
        self.done = False

        for index, value in enumerate(self.text):
            legal_cells  = [span[index][1]for span in self.spans]
            illegal_cells = [cell for cell in cells if cell not in legal_cells and value in cell.possible_values]
            Cell.remove_value_from_cells(illegal_cells, value)

    def check(self, sudoku: Sudoku) -> True:
        if self.done:
            return False
        for span in self.spans:
            for value, cell in span:
                if cell.is_known and cell.known_value == value:
                    assert all(val in cel.possible_values for (val, cel) in span)
                    unknowns = [(val, cel) for (val, cel) in span if not cel.is_known]
                    if unknowns:
                        print(f"We can definitely place {self.text} starting at {span[0][1].index}")
                        for val, cel in unknowns:
                            cel.set_value_to(val, show=True)
                    self.done = True
                    return True
        for span in self.spans:
            for value, cell in span:
                if value not in cell.possible_values:
                    unknowns =  [(val, cel) for (val, cel) in span if val in cel.possible_values]
                    if unknowns:
                        print(f"Text {self.text} definitely doesn't start at {span[0][1].index}")
                        for val, cel in unknowns:
                            Cell.remove_value_from_cells([cel], val)
                        return True
        return False


class ThermometerFeature(Feature):
    thermometer: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, thermometer: Sequence[Tuple[int, int]]):
        self.thermometer = thermometer

    def initialize(self, sudoku: Sudoku) -> None:
        self.cells = [sudoku.grid.matrix[x] for x in self.thermometer]
        length = len(self.thermometer)
        span = 10 - length  # number of values each element in thermometer can have
        for minimum, cell in enumerate(self.cells, start=1):
            maximum = minimum + span - 1
            bad_values = list(range(1, minimum)) + list(range(maximum + 1, 10))
            Cell.remove_values_from_cells([cell], set(bad_values))

    def check(self, sudoku: Sudoku) -> True:
        previous_cells = itertools.chain([None], self.cells)
        next_cells = itertools.chain(itertools.islice(self.cells, 1, None), itertools.repeat(None))
        for cell, previous_cell, next_cell in zip(self.cells, previous_cells, next_cells):
            impossible = set()
            for value in cell.possible_values:
                if previous_cell and value <= min(previous_cell.possible_values):
                    impossible.add(value)
                elif next_cell and value >= max(next_cell.possible_values):
                    impossible.add(value)
            if impossible:
                print("No appropriate value in adjacent cell")
                Cell.remove_values_from_cells([cell], impossible)
                return True
        return False

    def draw(self, sudoku: Sudoku) -> None:
        self.draw_line(self.thermometer, color='lightgrey', linewidth=5)
        row, column = self.thermometer[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


class EvenFeature(Feature):
    evens: Sequence[Tuple[int, int]]

    def __init__(self, evens: Sequence[Tuple[int, int]]):
        self.evens = evens

    def initialize(self, sudoku: Sudoku) -> None:
        cells = [sudoku.grid.matrix[x] for x in self.evens]
        Cell.remove_values_from_cells(cells, {1, 3, 5, 7, 9})

    def check(self, sudoku: Sudoku) -> bool:
        pass





def merge(p1: str, p2: str) -> str:
    assert len(p1) == len(p2) == 81
    assert(p1[i] == '.' or p2[i] == '.' or p1[i] == p2[i] for i in range(81))
    result = ((y if x == '.' else x) for x, y in zip(p1, p2))
    return ''.join(result)


def puzzle1() -> None:
    # XUZZ = "123456789123456789123456789123456789123456789123456789123456789123456789123456789"
    puzzle = "...6.1.....4...2...1.....6.1.......2....8....6.......4.7.....9...1...4.....1.2..3"
    texts = [(3, 1, 8), *[(x, 9) for x in range(1, 9)]]
    features: List[Feature] = [ContainsTextFeature(i, text) for i, text in enumerate(texts, start=1)]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)
    sudoku.draw_grid()


def puzzle2():
    previo = '...........................................5........3.............7..............'
    puzzle = '.9...16....................8............9............8....................16...8.'
    puzzle = merge(puzzle, previo)
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=[MalvoloRingFeature()])
    sudoku.draw_grid()


def puzzle3() -> None:
    previo = '....4........6.............8.....9..........6.........2..........................'
    puzzle = '..9...7...5.....3.7.4.....9.............5.............5.....8.1.3.....9...7...5..'

    evens = [(2, 3), (3, 2), (3, 3), (1, 4), (1, 5), (1, 6)]
    evens = evens + [(column, 10 - row) for row, column in evens]
    evens = evens + [(10 - row, 10 - column) for row, column in evens]

    features = [SnakeFeature([(3, 6), (3, 5), (4, 4), (5, 4), (5, 5), (5, 6), (6, 6), (7, 5), (7, 4)]),
                EvenFeature(evens),
                ]
    sudoku = Sudoku()
    sudoku.solve(merge(puzzle, previo), features=features)
    sudoku.draw_grid()


def puzzle4():
    previo = '.......................1....4..................5...1.............................'
    puzzle = '...............5.....6.....' + (54 * '.')
    puzzle = merge(puzzle, previo)
    info1 = ((1, 2), (2, 2), (3, 3), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (8, 3))
    info2 = tuple((row, 10-column) for (row, column) in info1)
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=[GermanSnakeFeature(info1), GermanSnakeFeature(info2)], knight=True)
    sudoku.draw_grid()


def puzzle5() -> None:
    previo = '..7......3.....5......................3..8............15.............9....9......'
    puzzle = '......3...1...............72.........................2..................8........'
    diadem = SnakeFeature([(4, 2), (2, 1), (3, 3), (1, 4), (3, 5), (1, 6), (3, 7), (2, 9), (4, 8)])
    thermometers = [ThermometerFeature([(row, column) for row in (9, 8, 7, 6, 5, 4)]) for column in (2, 4, 6, 8)]
    features = [diadem, *thermometers]
    sudoku = Sudoku()
    sudoku.solve(merge(puzzle, previo), features=features)
    sudoku.draw_grid()

def run_thermometer():
    thermometers = [[(2, 2), (1, 3), (1, 4), (1, 5), (2, 6)],
                    [(2, 2), (3, 1), (4, 1), (5, 1), (6, 2)],
                    [(2, 3), (2, 4), (2, 5), (3, 6), (3, 7), (4, 8)],
                    [(2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (6, 8)],
                    [(3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 7)],
                    [(4, 2), (5, 2), (6, 3), (7, 4), (8, 4)],
                    [(1, 7), (1, 8)],
                    [(8, 8), (8, 9)],
                    [(8, 2), (8, 3)]]
    puzzle = ' ' * 81
    features = [ThermometerFeature(thermometer) for thermometer in thermometers]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)
    sudoku.draw_grid()

if __name__ == '__main__':
    puzzle3()


