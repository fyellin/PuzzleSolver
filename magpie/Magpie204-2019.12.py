import functools
import itertools
from collections.abc import Sequence, Iterable

from matplotlib import pyplot as plt

from solver import Clue, ClueValue, ConstraintSolver, generators, Intersection, \
    DancingLinks, Location, ClueValueGenerator, KnownClueDict

LENGTHS = (
    # 1a 4a 5a 4d 2d 3d
    (3, 3, 2, 2, 3, 3, (3, 1)),
    (2, 3, 3, 2, 3, 3, (3, 1)),
    (3, 2, 3, 2, 3, 2, (3, 1)),
    (2, 3, 2, 2, 2, 3, (3, 2)),
    (2, 3, 3, 2, 3, 2, (3, 1)),
    (3, 3, 2, 2, 3, 3, (3, 1)),
    (3, 2, 3, 2, 3, 2, (3, 1)),
    (3, 3, 3, 2, 3, 3, (3, 1)),
    (3, 2, 3, 2, 2, 3, (3, 1)),
)

PRIMES = tuple(itertools.takewhile(lambda x: x < 1000, generators.prime_generator()))


@functools.lru_cache(maxsize=None)
def all_different(value: int) -> bool:
    temp = str(value)
    return len(set(temp)) == len(temp)


def make_generator(numbers: Iterable[int]) -> ClueValueGenerator:
    temp = list(numbers)

    def generator(clue: Clue) -> Iterable[int]:
        min_value, max_value = generators.get_min_max(clue)
        for number in temp:
            if min_value <= number < max_value and all_different(number):
                yield number
    return generator


GENERATOR_1a = make_generator([prime1 * prime2 for prime1 in PRIMES for prime2 in PRIMES if prime1 <= prime2])
GENERATOR_4a = make_generator([x * x for x in range(40)])
GENERATOR_5a = make_generator(itertools.takewhile(lambda x: x < 1000, (i * (i + 1) // 2 for i in itertools.count(1))))
GENERATOR_2d = make_generator(range(10, 1000, 5))
GENERATOR_3d = make_generator(range(10, 1000))
GENERATOR_4d = make_generator({x ** 2 + y ** 2 for x in range(1, 32) for y in range(x + 1, 32)})


def create_all_grids() -> Sequence["Solver204"]:
    result = [
        Solver204.create(length_1a, length_4a, length_5a, length_2d, length_3d, location_5a)
        for length_1a, length_4a, length_5a, length_2d, length_3d in itertools.product((2, 3), repeat=5)
        for location_5a in ((3, 1), (3, 2))
        if location_5a == (3, 1) or length_5a == 2  # length_5a can't be 3 if starting at (3, 2)
        # if length_3d == 3 or length_5a == 3 or location_5a == (3, 2)  # square (3, 3) must be filled
    ]
    return result


class Solver204(ConstraintSolver):
    grid: str
    _answers: list[tuple[tuple[str, ...], str, str]]

    @staticmethod
    def create(length_1a: int, length_4a: int, length_5a: int, length_2d: int, length_3d: int,
               location_5a: Location, grid: str | None = None) -> "Solver204":
        clues = [
            Clue('1a', True, (1, 1), length_1a, generator=GENERATOR_1a),
            Clue('4a', True, (2, 1), length_4a, generator=GENERATOR_4a),
            Clue('5a', True, location_5a, length_5a, generator=GENERATOR_5a),
            Clue('2d', False, (1, 2), length_2d, generator=GENERATOR_2d),
            Clue('3d', False, (1, 3), length_3d, generator=GENERATOR_3d),
            Clue('4d', False, (2, 1), 2, generator=GENERATOR_4d)
        ]
        grid = grid or f'{length_1a}{length_4a}{length_5a}{length_2d}{length_3d}{location_5a[1]}'
        return Solver204(grid, clues)

    @staticmethod
    def create_for_grid(grid: int) -> "Solver204":
        length_1a, length_4a, length_5a, length_4d, length_2d, length_3d, location_5a = LENGTHS[grid - 1]
        assert length_4d == 2
        return Solver204.create(length_1a, length_4a, length_5a, length_2d, length_3d, location_5a, str(grid))

    def __init__(self, grid: str, clue_list: Sequence[Clue]):
        super().__init__(clue_list)
        self.grid = grid
        for x, y in itertools.combinations(self._clue_list, 2):
            if Intersection.get_intersections(x, y):
                self.add_constraint((x, y), self.mutual_constraint_intersects)
            else:
                self.add_constraint((x, y), self.mutual_constraint_no_intersect)
        self.add_constraint(self._clue_list, self.constraint_3d)

    @staticmethod
    @functools.lru_cache(None)
    def mutual_constraint_intersects(clue1: ClueValue, clue2: ClueValue) -> bool:
        temp = clue1 + clue2
        return len(set(temp)) == len(temp) - 1

    @staticmethod
    @functools.lru_cache(None)
    def mutual_constraint_no_intersect(clue1: ClueValue, clue2: ClueValue) -> bool:
        temp = clue1 + clue2
        return len(set(temp)) == len(temp)

    @staticmethod
    def constraint_3d(a1: ClueValue, a4: ClueValue, a5: ClueValue, d2: ClueValue, d3: ClueValue, d4: ClueValue) -> bool:
        @functools.lru_cache(None)
        def sum_of_digits(n: ClueValue) -> int:
            return sum(map(int, n))

        values = list(map(sum_of_digits, (d3, a1, a4, a5, d2, d4)))
        count = values.count(values[0])
        return count == 2

    def solve(self, *, show_time: bool = True, debug: bool = False, max_debug_depth: int | None = None) -> int:
        self._answers = []
        return super().solve(show_time=False, debug=debug, max_debug_depth=max_debug_depth)

    def get_allowed_regexp(self, location: Location) -> str:
        if len(self.grid) > 5:
            return '[^0]'
        return super().get_allowed_regexp(location)

    def show_solution(self, known_clues: KnownClueDict) -> None:
        values = tuple(known_clues[clue] for clue in self._clue_list)
        location_dict = {location: digit
                         for clue, clue_value in known_clues.items()
                         for location, digit in zip(clue.locations, clue_value)}
        if (3, 3) not in location_dict:
            location_dict[3, 3] = (set("123456789") - set(location_dict.values())).pop()
        grid_fill = ''.join(location_dict[row, column] for row in range(1, 4) for column in range(1, 4))
        missing = next(x for x in "0123456789" if x not in grid_fill)
        self._answers.append((values, grid_fill, missing))

    def values_to_known_clue_dict(self, values: tuple[str, ...]) -> KnownClueDict:
        return {clue: ClueValue(value) for clue, value in zip(self._clue_list, values)}

    def get_answers(self) -> list[tuple[tuple[str, ...], str, str]]:
        return self._answers

    def __repr__(self) -> str:
        return f"<{self.grid}>"


def run() -> None:
    all_constraints = {}
    all_values: set[str] = set()
    for grid in range(1, 10):
        solver = Solver204.create_for_grid(grid)
        solver.solve(debug=False)
        for values, grid_fill, missing in solver.get_answers():
            if missing != '0':
                constraints = [f"grid-{grid}", f"missing-{missing}"]
                constraints.extend(f"grid-{grid}-has-{v}" for v in grid_fill)
                constraints.extend(values)
                all_values.update(values)
                all_constraints[(solver, values)] = constraints

    for solver in create_all_grids():
        solver.solve(debug=False)
        for values, grid_fill, missing in solver.get_answers():
            assert missing == '0'
            constraints = ['submission']
            constraints.extend(f"grid-{xgrid}-has-{v}" for xgrid, v in enumerate(grid_fill, start=1))
            all_constraints[(solver, values)] = constraints

    dancing_links = DancingLinks(all_constraints, row_printer=my_row_printer, optional_constraints=all_values)
    dancing_links.solve(recursive=True)


def my_row_printer(constraint_names: Sequence[tuple[Solver204, tuple[str, ...]]]) -> None:
    print(constraint_names)
    figure, axes = plt.subplots(4, 3, figsize=(8, 11), dpi=100, gridspec_kw={'wspace': .05, 'hspace': .05})

    for solver, values in constraint_names:
        clue_solutions = solver.values_to_known_clue_dict(values)
        grid = int(solver.grid)
        if 1 <= grid <= 9:
            solver.plot_board(clue_solutions, axes=axes[divmod(grid - 1, 3)])
        else:
            axes[3, 0].axis('off')
            axes[3, 2].axis('off')
            solver.plot_board(clue_solutions, axes=axes[3, 1])
    plt.show()


if __name__ == '__main__':
    run()
