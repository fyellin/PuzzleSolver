import functools
import itertools

from solver import (
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

ACROSS = "23/32/23/32/11111/23/32/23/32"
DOWN = "111111111/414/414/414/111111111"
FAST_PASS = False


class Listener4908(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False, max_debug_depth=4)

    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        clue_map = {clue.name: clue for clue in clues}
        self.last_locations = {clue.locations[-1] for clue in clue_map.values()}
        for clue in clue_map.values():
            clue.ll_indices = frozenset(i for i, location in enumerate(clue.locations)
                                        if location in self.last_locations)

        super().__init__(list(clue_map.values()))
        self.add_puzzle_constraints(clue_map)
        self.add_no_duplicates_within_value_constraints(clue_map)
        self.add_no_duplicate_on_side_constraints(clue_map)

    @functools.cache
    def get_bitmap(self, value: ClueValue, ll_indices: frozenset[int]) -> int:
        result = 0
        for index, letter in enumerate(value):
            digit = int(letter)
            result |= 1 << (digit + 10 * (index in ll_indices))
        if result.bit_count() != len(value):
            raise ValueError
        return result

    def add_puzzle_constraints(self, clue_map: dict[str, Clue]) -> None:
        even = generators.filterer(lambda x: int(x) % 2 == 0)
        odd = generators.filterer(lambda x: int(x) % 2 == 1)
        rev = self.rev
        square2 = generators.known(*[2 * x * x for x in range(1, 10)])

        self.add_left_right_constraints(clue_map, "1a", "11a", rev(square), rev(triangular))
        self.add_left_right_constraints(clue_map, "3a", "13a", prime, palindrome)
        self.add_left_right_constraints(clue_map, "5a", "15a", palindrome, triangular)
        self.add_left_right_constraints(clue_map, "6a", "16a", triangular, even)
        self.add_left_right_constraints(clue_map, "7a", "17a", odd, square2)
        self.add_left_right_constraints(clue_map, "8a", "18a", square, triangular)
        self.add_left_right_constraints(clue_map, "9a", "19a", square, rev(square))
        self.add_left_right_constraints(clue_map, "10a", "20a", fibonacci, prime)

        self.add_left_right_constraints(clue_map, "2d", "12d", prime, square)
        self.add_left_right_constraints(clue_map, "4d", "14d", prime, triangular)
        self.clue_named("3d").generator = self.clue_named("13d").generator = allvalues
        self.add_extended_constraint("3d 3a 6a", extended_multiply_constraint)
        self.add_extended_constraint("13d 17a 19a", extended_multiply_constraint)

        # 6a has to be < 20 for the multiplication to work. But then 3d can't start with
        # a 1 (as 6a also starts with a 1), so 6a has to be < 15. 6a can't be 10 as both
        # 6a and 3d would end with 0.
        self.add_constraint("6a", lambda x: 10 < int(x) < 15)

        if FAST_PASS:
            self.clue_named("10a").generator = generators.known(59)
            self.clue_named("20a").generator = generators.known(34)
            self.clue_named("1a").generator = generators.known(94)
            self.clue_named("11a").generator = generators.known(82)
            self.clue_named('4d').generator = generators.known(2145)

    def add_left_right_constraints(self, clue_map, name1, name2, generator1, generator2):
        clue1, clue2 = clue_map[name1], clue_map[name2]
        assert clue1.length == clue2.length
        values1 = frozenset(ClueValue(str(x)) for x in generator1(clue1))
        values2 = frozenset(ClueValue(str(x)) for x in generator2(clue2))
        values = values1 | values2
        clue1.generator = clue2.generator = generators.known(*values)

        def is_separate(start_values: list[ClueValue],
                        v1: ClueValue | None, v2: ClueValue | None) -> list[ClueValue]:
            if v1 is None:
                v1 = v2
            if v1 not in values1:
                return [x for x in start_values if x in values1]
            if v1 not in values2:
                return [x for x in start_values if x in values2]
            return start_values

        self.add_extended_constraint((clue1, clue2), is_separate,
                                     name=f"{clue1.name}-{clue2.name}-lr")

    def add_no_duplicates_within_value_constraints(self, clue_map: dict[str, Clue]
                                                   ) -> None:
        for clue in clue_map.values():
            def is_good_value(value: str, ll_indices=clue.ll_indices):
                try:
                    self.get_bitmap(value, ll_indices)
                    return True
                except ValueError:
                    return False
            self.add_constraint((clue,), is_good_value, name=f'{clue.name}')

    def add_no_duplicate_on_side_constraints(self, clue_map: dict[str, Clue]) -> None:
        for clue1, clue2 in itertools.combinations(clue_map.values(), 2):
            if (clue1.base_location[0] <= 4) != (clue2.base_location[0] <= 4):
                continue
            is_disjoint = clue1.location_set.isdisjoint(clue2.location_set)

            def test_single_value(values, v1, v2,
                                  ll_indices1=clue1.ll_indices,
                                  ll_indices2=clue2.ll_indices,
                                  is_disjoint=is_disjoint):
                if v2 is None:
                    known_value, known_indices, unknown_indices = v1, ll_indices1, ll_indices2
                else:
                    known_value, known_indices, unknown_indices = v2, ll_indices2, ll_indices1
                known_bitmap = self.get_bitmap(known_value, known_indices)
                if is_disjoint:
                    r = [x for x in values
                         if self.get_bitmap(x, unknown_indices) & known_bitmap == 0]
                else:
                    r = [x for x in values
                         if (t := self.get_bitmap(x, unknown_indices) & known_bitmap)
                         if t & (t - 1) == 0]
                return r

            self.add_extended_constraint((clue1, clue2), test_single_value,
                                         name=f'{clue1.name}-{clue2.name}')

    @staticmethod
    def rev(generator: ClueValueGenerator) -> ClueValueGenerator:
        def new_generator(clue):
            items = [str(x) for x in generator(clue)]
            return [item[::-1] for item in items if item[-1] != '0']
        return new_generator

    def draw_grid(self, location_to_clue_numbers, **args) -> None:
        for location, values in location_to_clue_numbers.items():
            for index, value in enumerate(values):
                if int(value) > 10:
                    values[index] = int(value) - 10
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers,
                          blacken_unused=False, **args)


def extended_multiply_constraint(values, a, b, c) -> list[ClueValue]:
    if a is None:
        result = int(b) * int(c)
    else:
        result, r = divmod(int(a), int(b if c is None else c))
        if r != 0:
            return []
    result = str(result)
    return [result] if result in values else []


if __name__ == '__main__':
    Listener4908.run()
