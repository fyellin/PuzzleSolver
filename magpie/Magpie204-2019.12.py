import functools
import itertools
from typing import Sequence, List, Tuple, Union, Set, Iterable, Optional

from matplotlib import pyplot as plt

from solver import Clue, ClueValue, ConstraintSolver, generators, Intersection, \
    DancingLinks, Location, ClueValueGenerator
from solver.equation_solver import KnownClueDict

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


def constraint_3d(a1: ClueValue, a4: ClueValue, a5: ClueValue, d2: ClueValue, d3: ClueValue, d4: ClueValue) -> bool:
    @functools.lru_cache(None)
    def sum_of_digits(n: ClueValue) -> int:
        return sum(map(int, n))

    values = list(map(sum_of_digits, (d3, a1, a4, a5, d2, d4)))
    count = values.count(values[0])
    return count == 2


GENERATOR_1a = make_generator([prime1 * prime2 for prime1 in PRIMES for prime2 in PRIMES if prime1 <= prime2])
GENERATOR_4a = make_generator([x * x for x in range(40)])
GENERATOR_5a = make_generator(itertools.takewhile(lambda x: x < 1000, (i * (i + 1) // 2 for i in itertools.count(1))))
GENERATOR_2d = make_generator(range(10, 1000, 5))
GENERATOR_3d = make_generator(range(10, 1000))
GENERATOR_4d = make_generator({x ** 2 + y ** 2 for x in range(1, 32) for y in range(x + 1, 32)})


def create_solver(length_1a: int, length_4a: int, length_5a: int, length_2d: int, length_3d: int,
                  location_5a: Location, grid: Optional[str] = None) -> "Solver204":
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


def create_solver_for_grid(grid: int) -> "Solver204":
    length_1a, length_4a, length_5a, length_4d, length_2d, length_3d, location_5a = LENGTHS[grid - 1]
    assert length_4d == 2
    return create_solver(length_1a, length_4a, length_5a, length_2d, length_3d, location_5a, str(grid))


def create_solvers_for_submission() -> Sequence["Solver204"]:
    result = []
    for length_1a, length_4a, length_5a, length_2d, length_3d in itertools.product((2, 3), repeat=5):
        for location_5a in ((3, 1), (3, 2)):
            if location_5a == (3, 2) and length_5a == 3:
                continue
            if length_3d == 3 or length_5a == 3 or location_5a == (3, 2):
                solver = create_solver(length_1a, length_4a, length_5a, length_2d, length_3d, location_5a)
                result.append(solver)
    return result


def create_solver_from_grid_encoding(grid: str) -> "Solver204":
    length_1a, length_4a, length_5a, length_2d, length_3d, loc = [int(x) for x in grid]
    location_5a = (3, loc)
    return create_solver(length_1a, length_4a, length_5a, length_2d, length_3d, location_5a)


class Solver204(ConstraintSolver):
    grid: str
    answers: List[Tuple[Tuple[str, ...], str, str]]

    def __init__(self, grid: Union[int, str], clue_list: Sequence[Clue]):
        super().__init__(clue_list)
        a, b, c, d, e, f = self._clue_list
        self.grid = str(grid)
        for x, y in itertools.combinations((a, b, c, d, e, f), 2):
            if Intersection.get_intersections(x, y):
                self.add_constraint((x, y), Solver204.mutual_constraint_int)
            else:
                self.add_constraint((x, y), Solver204.mutual_constraint_xint)
        self.add_constraint((a, b, c, d, e, f), constraint_3d)

    @staticmethod
    @functools.lru_cache(None)
    def mutual_constraint_int(clue1: ClueValue, clue2: ClueValue) -> bool:
        temp = clue1 + clue2
        return len(set(temp)) == len(temp) - 1

    @staticmethod
    @functools.lru_cache(None)
    def mutual_constraint_xint(clue1: ClueValue, clue2: ClueValue) -> bool:
        temp = clue1 + clue2
        return len(set(temp)) == len(temp)

    def solve(self, *, show_time: bool = True, debug: bool = False, max_debug_depth: Optional[int] = None) -> int:
        self.answers = []
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
        grid_fill = ''.join(location_dict[row, column] for row in range(1, 4) for column in range(1, 4))
        missing = next(x for x in "0123456789" if x not in grid_fill)
        self.answers.append((values, grid_fill, missing))

    def get_answers(self) -> List[Tuple[Tuple[str, ...], str, str]]:
        return self.answers

    def values_from_grid_fill(self, grid_fill: str) -> KnownClueDict:
        def value_for_location(location: Location) -> str:
            (row, column) = location
            return grid_fill[row * 3 + column - 4]

        def value_for_clue(clue: Clue) -> ClueValue:
            letters = [value_for_location(location) for location in clue.locations]
            return ClueValue(''.join(letters))

        return {clue: value_for_clue(clue) for clue in self._clue_list}


def run() -> None:
    all_constraints = {}
    all_values: Set[str] = set()
    for grid in "123456789":
        solver = create_solver_for_grid(int(grid))
        solver.solve(debug=False)
        for values, grid_fill, missing in solver.get_answers():
            if missing != '0':
                constraints = [f"grid-{grid}", f"missing-{missing}"]
                constraints.extend(f"grid-{grid}-{v}" for v in grid_fill)
                constraints.extend(values)
                all_values.update(values)
                name = f"GRID-{grid}-{grid_fill}"
                all_constraints[name] = constraints

    for solver in create_solvers_for_submission():
        solver.solve(debug=False)
        for values, grid_fill, missing in solver.get_answers():
            assert missing == '0'
            constraints = ['submission']
            constraints.extend(f"grid-{xgrid}-{v}" for xgrid, v in enumerate(grid_fill, start=1))
            name = f"SOLUTION-{solver.grid}-{grid_fill}"
            all_constraints[name] = constraints

    dancing_links = DancingLinks(all_constraints, row_printer=my_row_printer, optional_constraints=all_values)
    dancing_links.solve(debug=0)


def my_row_printer(constraint_names: Sequence[str]) -> None:
    print(sorted(constraint_names))

    figure, axes = plt.subplots(4, 3, figsize=(8, 11), dpi=100, gridspec_kw={'wspace': .05, 'hspace': .05})

    for i in range(1, 11):
        if i == 10:
            constraint = next(x for x in constraint_names if x.startswith('SOLUTION'))
            _, grid, grid_fill = constraint.split('-')
            solver = create_solver_from_grid_encoding(grid)
        else:
            constraint = next(x for x in constraint_names if x.startswith(f'GRID-{i}'))
            _, grid, grid_fill = constraint.split('-')
            assert int(grid) == i
            solver = create_solver_for_grid(i)
        clue_solutions = solver.values_from_grid_fill(grid_fill)
        if i != 10:
            solver.plot_board(clue_solutions, axes=axes[divmod(i - 1, 3)])
        else:
            axes[3, 0].axis('off')
            axes[3, 2].axis('off')
            solver.plot_board(clue_solutions, axes=axes[3, 1])
    # plt.show()


if __name__ == '__main__':
    run()
    if False:
        t = ['GRID-1-278361450', 'GRID-2-657841903', 'GRID-3-749810253', 'GRID-4-384256091',
             'GRID-5-351729406', 'GRID-6-398625107', 'GRID-7-287496105', 'GRID-8-842169703',
             'GRID-9-974258630', 'SOLUTION-333321-926784351']
        my_row_printer(t)

