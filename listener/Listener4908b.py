from solver import (
    Clue,
    Clues,
    ClueValue,
    ConstraintSolver,
    DancingLinks,
    Intersection,
    Orderer,
    generators,
)
from solver.generators import (
    ClueValueGenerator,
    fibonacci,
    palindrome,
    prime,
    square,
    triangular,
)

ACROSS = "23/32/23/32/11111/23/32/23/32"
DOWN = "111111111/414/414/414/111111111"


class Listener4908 (ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.dancing_links.solve(debug=10)

    def __init__(self):
        self.clues = clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        super().__init__(clues)
        self.clue_map = clue_map = {clue.name: clue for clue in clues}
        self.last_locations = {clue.locations[-1] for clue in clue_map.values()}
        self.constraints = {}
        self.optional_constraints = {
            # These are colored to indicate the value in that square
            *[f'r{r}c{c}'
              for r in range(1, 10) for c in range(1, 6) if r != 5],
            # These are colored with the location containing the digit that is
            # on the left/right side of the grid in the not-final/final square
            *[f'{ch}-{lr}-{fl}' for ch in range(10) for lr in "LR" for fl in "FL"],
        }
        self.add_puzzle_constraints()
        self.dancing_links = DancingLinks(
            self.constraints,
            optional_constraints=self.optional_constraints,
            row_printer=self.my_row_printer)

    def add_puzzle_constraints(self) -> None:
        even = generators.filterer(lambda x: int(x) % 2 == 0)
        odd = generators.filterer(lambda x: int(x) % 2 == 1)
        square2 = generators.known(*[2 * x * x for x in range(1, 10)])

        def rev(generator: ClueValueGenerator) -> ClueValueGenerator:
            def new_generator(clue):
                items = [str(x) for x in generator(clue)]
                return [item[::-1] for item in items if item[-1] != '0']
            return new_generator

        self.add_left_right_constraints("1a", "11a", rev(square), rev(triangular))
        self.add_left_right_constraints("3a", "13a", prime, palindrome)
        self.add_left_right_constraints("5a", "15a", palindrome, triangular)
        self.add_left_right_constraints("6a", "16a", triangular, even)
        self.add_left_right_constraints("7a", "17a", odd, square2)
        self.add_left_right_constraints("8a", "18a", square, triangular)
        self.add_left_right_constraints("9a", "19a", square, rev(square))
        self.add_left_right_constraints("10a", "20a", fibonacci, prime)
        self.add_left_right_constraints("2d", "12d", prime, square)
        self.add_left_right_constraints("4d", "14d", prime, triangular)
        # These must come last, since they use the code above to determine legal values.
        self.add_multiply_constraints("6a", "3a", "3d")
        self.add_multiply_constraints("17a", "19a", "13d")

    def add_left_right_constraints(self, name1, name2, generator_a, generator_b):
        constraints = self.constraints
        clue1, clue2 = self.clue_map[name1], self.clue_map[name2]
        assert clue1.length == clue2.length
        values_a = {str(x) for x in generator_a(clue1)}
        values_b = {str(x) for x in generator_b(clue1)}
        pattern_generator = Intersection.make_pattern_generator(clue1, (), self)
        orderer = None
        pattern = pattern_generator({})

        if duplicates := values_a & values_b:
            # If it turns out that the solution has a double duplicate (which it does),
            # then we force there to be only one solution by forcing the left side to
            # be generator_a and the right side to be generator_b
            orderer = Orderer.LE(f'{clue1.name}-orderer', 2)
            self.optional_constraints.update(orderer.all_codes())
        for clue, side in ((clue1, 'L'), (clue2, 'R')):
            for values, which_gen in ((values_a, 'A'), (values_b, 'B')):
                for value in values:
                    if not pattern.fullmatch(value):
                        continue
                    unique = self._get_uniqueness_map(clue, value, side)
                    if unique is None:
                        continue
                    constraint = [f'Clue-{clue.name}',
                                  f'Z{clue1.name}-{clue2.name}-{which_gen}',
                                  *unique.items(),
                                  *clue.dancing_links_rc_constraints(value)]
                    if value in duplicates:  # noqa: SIM102
                        ordering = orderer.left if side == 'L' else orderer.right
                        constraint.extend(ordering(which_gen == 'B'))
                    constraints[clue, value, which_gen] = constraint

    def add_multiply_constraints(self, clue2_name, clue3_name, clue4_name):
        clue2, clue3, clue4 = map(self.clue_map.get, (clue2_name, clue3_name, clue4_name))
        side = 'L' if clue2.base_location[0] <= 4 else 'R'
        intersection, = Intersection.get_intersections(clue3, clue4)
        values2 = sorted({key[1] for key in self.constraints if key[0] == clue2})
        values3 = sorted({key[1] for key in self.constraints if key[0] == clue3})
        for value2 in values2:
            for value3 in values3:
                value4 = str(int(value2) * int(value3))
                if len(value4) != 4:
                    continue
                if value4[intersection.other_index] != value3[intersection.this_index]:
                    continue
                unique4 = self._get_uniqueness_map(clue4, value4, side)
                if unique4 is None:
                    # Never mind if this value has illegal duplicate digits
                    continue
                unique2 = self._get_uniqueness_map(clue2, value2, side)
                unique3 = self._get_uniqueness_map(clue3, value3, side)
                all_uniques = unique2 | unique3 | unique4
                # Except for the intersection, we must have 8 unique digits
                if len(all_uniques) != 8:
                    continue
                locations_to_values = (
                        dict(clue2.dancing_links_rc_constraints(value2)) |
                        dict(clue3.dancing_links_rc_constraints(value3)) |
                        dict(clue4.dancing_links_rc_constraints(value4)))
                constraint = [f'Clue-{clue4.name}',
                              *all_uniques.items(),
                              *locations_to_values.items(),]
                self.constraints[clue4, value4, f'{value2} x {value3}'] = constraint

    def _get_uniqueness_map(self, clue: Clue, value: ClueValue, side: str
                            ) -> dict[str, str] | None:

        # Create a map from the secondary constraint indication that
        #    digit - left-or-right-side - not-final-or-final
        # to the location where that occurs. This coloring prevents any other clue
        # from putting that constraint elsewhere.
        result = {f'{ch}-{side}-{'FL'[(r, c) in self.last_locations]}': f'r{r}c{c}'
                  for ch, (r, c) in zip(value, clue.locations)}
        # If len(result) != clue.length, this value has an illegal duplicated letter
        return result if len(result) == clue.length else None

    def my_row_printer(self, rows):
        clue_values = {item[0]: item[1] for item in rows if isinstance(item, tuple)}
        self.plot_board(clue_values)

    def draw_grid(self, location_to_clue_numbers, **args) -> None:
        for location, values in location_to_clue_numbers.items():
            for index, value in enumerate(values):
                if int(value) > 10:
                    values[index] = int(value) - 10
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers,
                          blacken_unused=False, **args)


if __name__ == '__main__':
    Listener4908.run()
