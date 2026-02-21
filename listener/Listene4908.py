import itertools
from collections import Counter
from collections.abc import Sequence
from typing import Any

from solver import (
    AbstractLetterCountHandler,
    Clue,
    Clues,
    ClueValue,
    ConstraintSolver,
    generators,
)
from solver.generators import (
    ClueValueGenerator,
    allvalues,
    fibonacci,
    palindrome,
    prime,
    square,
    triangular,
)

ACROSS = "23/32/23/32/23/32/23/32"
DOWN = "11111111/44/44/44/11111111"

"""
9 4 3 2 3
8 0 8 1 2
5 0 7 4 1
6 7 6 5 9

8 2 3 6 7
5 9 5 7 8
2 1 4 0 0
1 6 9 3 4
"""

class Listener4908(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True, max_debug_depth=4)

    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        clue_map = {clue.name: clue for clue in clues}
        super().__init__(list(clue_map.values()))
        self.add_my_constraints(clue_map)
        self.add_within_clue_constraints(clue_map)
        self.add_within_grid_constraints(clue_map)

    def add_my_constraints(self, clue_map: dict[str, Clue]) -> None:
        even = generators.filterer(lambda x: int(x) % 2 == 0)
        odd = generators.filterer(lambda x: int(x) % 2 == 1)
        rev = self.rev
        square2 = generators.known(*[2 * x * x for x in range(1, 10)])

        self.lr_constraints(clue_map, "1a", "11a", rev(square), rev(triangular))
        # self.clue_named("1a").generator = generators.known(94)
        # self.clue_named("11a").generator = generators.known(82)

        self.lr_constraints(clue_map, "3a", "13a", prime, palindrome)
        self.lr_constraints(clue_map, "5a", "15a", palindrome, triangular)
        self.lr_constraints(clue_map, "6a", "16a", triangular, even)
        self.lr_constraints(clue_map, "7a", "17a", odd, square2)
        self.lr_constraints(clue_map, "8a", "18a", square, triangular)
        self.lr_constraints(clue_map, "9a", "19a", square, rev(square))
        self.lr_constraints(clue_map, "10a", "20a", fibonacci, prime)
        # self.clue_named("10a").generator = generators.known(59)
        # self.clue_named("20a").generator = generators.known(34)

        self.lr_constraints(clue_map, "2d", "12d", prime, square)
        self.lr_constraints(clue_map, "4d", "14d", prime, triangular)
        self.clue_named("3d").generator = self.clue_named("13d").generator = allvalues
        self.add_constraint("3d 3a 6a", lambda x, y, z: int(x) == int(y) * int(z))
        self.add_constraint("13d 17a 19a", lambda x, y, z: int(x) == int(y) * int(z))
        # self.clue_named('4d').generator = generators.known(2145)

    def lr_constraints(self, clue_map, name1, name2, generator1, generator2):
        clue1, clue2 = clue_map[name1], clue_map[name2]
        assert clue1.length == clue2.length
        values1 = frozenset(ClueValue(str(x)) for x in generator1(clue1))
        values2 = frozenset(ClueValue(str(x)) for x in generator2(clue2))
        values = values1 | values2
        clue1.generator = clue2.generator = generators.known(*values)

        def is_separate(start_values: list[ClueValue],
                        v1: ClueValue | None, v2: ClueValue | None) -> list[ClueValue]:
            if v1 is None:
                v1, v2 = v2, v1
            if v1 not in values:
                assert False, "This is broken"
            if v1 not in values1:
                return [x for x in start_values if x in values1]
            if v1 not in values2:
                return [x for x in start_values if x in values2]
            return start_values

        self.add_extended_constraint((clue1, clue2), is_separate,
                                     name=f"{clue1.name}{clue2.name}")

    def add_within_clue_constraints(self, clue_map: dict[str, Clue]) -> None:
        last_locations = {clue.locations[-1] for clue in clue_map.values()}
        for clue in clue_map.values():
            indices_partition = [], []
            for i, location in enumerate(clue.locations):
                indices_partition[location in last_locations].append(i)
            for indices in indices_partition:
                if len(indices) >= 2:
                    tester = self.create_single_tester_function(indices)
                    self.add_constraint((clue,), tester, name=f'{clue.name}')

    def create_single_tester_function(self, indices: list[int]):
        length = len(indices)
        def test_value(value: ClueValue):
            letters = {value[i] for i in indices}
            return len(letters) == length
        return test_value

    def add_within_grid_constraints(self, clue_map: dict[str, Clue]) -> None:
        last_locations = {clue.locations[-1] for clue in clue_map.values()}
        for clue1, clue2 in itertools.combinations(clue_map.values(), 2):
            if (clue1.base_location[0] <= 4) != (clue2.base_location[0] <= 4):
                continue
            locations = clue1.location_set.symmetric_difference(clue2.location_set)
            locations = (frozenset(x for x in locations if x in last_locations),
                         frozenset(x for x in locations if x not in last_locations))
            clue1_indices = [[i for i, loc in enumerate(clue1.locations) if loc in location]
                             for location in locations]
            clue2_indices = [[i for i, loc in enumerate(clue2.locations) if loc in location]
                             for location in locations]
            for clue1_index, clue2_index in zip(clue1_indices, clue2_indices):
                if clue1_index and clue2_index:
                    tester = self.create_tester_function(clue1_index, clue2_index)
                    self.add_extended_constraint((clue1, clue2), tester, name=f'{clue1.name}{clue2.name}')

    def create_tester_function(self, clue1_indices, clue2_indices):
        expected_length = len(clue1_indices) + len(clue2_indices)
        def is_separate(start_values: list[ClueValue],
                        v1: ClueValue | None, v2: ClueValue | None) -> list[ClueValue]:
            assert (v1 is None) + (v2 is None) == 1
            if v2 is None:
                value, value_indices, unknown_indices = v1, clue1_indices, clue2_indices
            else:
                value, value_indices, unknown_indices = v2, clue2_indices, clue1_indices
            seen_letters = [value[i] for i in value_indices]
            new_values = []
            for start_value in start_values:
                new_value_letters = [start_value[i] for i in unknown_indices]
                if len(set(seen_letters) | set(new_value_letters)) == expected_length:
                    new_values.append(start_value)
            return new_values
        return is_separate

    @staticmethod
    def rev(generator: ClueValueGenerator) -> ClueValueGenerator:
        def new_generator(clue):
            items = [str(x) for x in generator(clue)]
            return [item[::-1] for item in items if item[-1] != '0']
        return new_generator

    def draw_grid(self, location_to_clue_numbers, **args) -> None:
        for location, values in location_to_clue_numbers.items():
            for index, value in enumerate(values):
                if (int(value) > 10):
                    values[index] = int(value) - 10
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers, **args)

if __name__ == '__main__':
    Listener4908.run()


