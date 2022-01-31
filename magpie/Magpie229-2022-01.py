from __future__ import annotations

import itertools
from collections.abc import Iterator, Sequence
from typing import Any, Union

from misc.primes import PRIMES
from solver import Clue, ClueValue, Clues, ConstraintSolver, generators
from solver.constraint_solver import Constraint


def digit_sum(value: ClueValue | str | int) -> int:
    return sum(int(x) for x in str(value))


def is_harshad(value: int) -> bool:
    digits = map(int, list(str(value)))
    return value % sum(digits) == 0


class TaggedString(str):
    tag: int

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f'{self.tag}.{self.value}'

    def __new__(cls, value: Union[int, str], tag: int) -> Any:
        return super().__new__(cls, value)  # type: ignore

    def __init__(self, value: Union[int, str], tag: int) -> None:
        super().__init__()
        self.value = str(value)
        self.tag = tag

    def __eq__(self, other) -> bool:
        return other is not None and super().__eq__(other) and self.tag == other.tag

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.tag))

    def __lt__(self, other) -> bool:
        return (self.value, self.tag) < (other.value, other.tag)


GRID = """
XXXXX
X....
.X.X.
X.X..
"""

even_generator = generators.filterer(lambda x: x % 2 == 0)
harshad_generator = generators.filterer(lambda x: is_harshad(x))


def square_pyramidal_generator(clue: Clue) -> Iterator[int]:
    return generators.within_clue_limits(clue, itertools.accumulate(i * i for i in itertools.count(1)))


def balanced_prime_generator(clue: Clue) -> Iterator[int]:
    generator = (b for (a, _), (b, c) in itertools.pairwise(itertools.pairwise(PRIMES)) if c - b == b - a)
    return generators.within_clue_limits(clue, generator)


ACROSSES = [
    (1, 3, generators.palindrome, generators.square),
    (4, 2, generators.palindrome, generators.triangular),
    (6, 2, harshad_generator, generators.prime),
    (8, 2, even_generator, generators.allvalues),
    (9, 2, even_generator, generators.prime),
    (10, 3, balanced_prime_generator, generators.triangular)
]

DOWNS = [
    (2, 2, generators.prime, square_pyramidal_generator),
    (3, 4, generators.allvalues, generators.allvalues),
    (4, 2, generators.allvalues, generators.prime),
    (5, 3, even_generator, generators.triangular),
    (6, 3, generators.lucas, generators.triangular),
    (7, 2, even_generator, generators.palindrome),
    (8, 2, generators.prime, generators.square)
]


class Magpie229 (ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie229()
        solver.solve(debug=True, max_debug_depth=1000, start_clues=("1a", "2d"))

    @staticmethod
    def run2() -> None:
        solver = Magpie229()
        solver._max_debug_depth = 0
        a1 = solver.get_initial_values_for_clue(solver.clue_named("10a"))
        print(sorted(a1))


    def __init__(self) -> None:
        clues, constraints = self.get_clues()
        super().__init__(clues, constraints=constraints, allow_duplicates=True)
        self.terminal_locations = {clue.locations[-1] for clue in self._clue_list}
        self.add_puzzle_constraints()
        self.add_pairwise_constraints()

    def get_clues(self) -> tuple[Sequence[Clue], Sequence[Constraint]]:
        grid = Clues.get_locations_from_grid(GRID)
        clues, constraints = [], []
        for information, is_across in ((ACROSSES, True), (DOWNS, False)):
            for number, length, generator1, generator2 in information:
                r, c = grid[number - 1]
                generator = self.dual_generator(generator1, generator2)
                clue1 = Clue(f'{number}{"a" if is_across else "d"}', is_across, (r, c), length,
                             context='left', generator=generator)
                clue2 = Clue(f'{number + 10}{"a" if is_across else "d"}', is_across, (r + 5, c), length,
                             context='right', generator=generator)
                clues += [clue1, clue2]
                if clue1.name != '3d':
                    # The first clue is for one grid and the second clue is for the other grid
                    constraints.append(Constraint((clue1, clue2),
                                                  lambda x, y: x.tag != y.tag or x.tag == 3 or y.tag==3))
                else:
                    # For
                    constraints.append(Constraint((clue1,), lambda x: x.tag != 2))
                    constraints.append(Constraint((clue2,), lambda x: x.tag != 1))
        return clues, constraints

    @staticmethod
    def dual_generator(generator1, generator2):
        def generator(clue: Clue):
            one = set(str(x) for x in generator1(clue))
            two = set(str(x) for x in generator2(clue))
            yield from (TaggedString(x, 1) for x in one - two)
            yield from (TaggedString(x, 2) for x in two - one)
            yield from (TaggedString(x, 3) for x in one & two)

        return generator

    def add_puzzle_constraints(self):
        def constraint_8a(across, down):
            if across.tag != 2:
                return True
            total = str(int(across) + int(down))
            return total == total[::-1]

        def constraint_4d_7d(four, seven) -> bool:
            return four.tag != 1 or int(four) % int(seven) == 0

        def extended_constraint_3d(values, a, b, c) -> Sequence[ClueValue]:
            if a is None:
                result = int(b) * int(c)
                if result > 9999:
                    return []
            else:
                assert b is None or c is None
                result, r = divmod(int(a), int(b if c is None else c))
                if r != 0:
                    return []
            return [value for tag in (1, 2, 3) for value in [TaggedString(result, tag)] if value in values]

        self.add_constraint(("8a", "8d"), constraint_8a),
        self.add_constraint(("18a", "18d"), constraint_8a),
        self.add_constraint(("4d", "7d"), constraint_4d_7d),
        self.add_constraint(("14d", "17d"), constraint_4d_7d),
        self.add_extended_constraint(("3d", "1a", "2d"), extended_constraint_3d),
        self.add_extended_constraint(("13d", "20a", "18d"), extended_constraint_3d)

    def add_pairwise_constraints(self):
        def check_all_different(values, pairs):
            # Since this is only called on squares on the same side of the grid, we can also
            # use it to eliminate duplicates
            if len(values) == 2 and values[0].value == values[1].value:
                return False
            seen = set()
            for clue_index, value_index in pairs:
                value = values[clue_index][value_index]
                if value in seen:
                    return False
                seen.add(value)
            return True

        for count in (1, 2):
            for clues in itertools.combinations(self._clue_list, count):
                if count == 2 and clues[0].context != clues[1].context:
                    continue
                locations = {location: (location in self.terminal_locations, clue_index, location_index)
                             for clue_index, clue in enumerate(clues)
                             for location_index, location in enumerate(clue.locations)}
                terminals = tuple([(clue_index, location_index)
                                  for (is_terminal, clue_index, location_index) in locations.values() if is_terminal])
                others = tuple([(clue_index, location_index)
                                for (is_terminal, clue_index, location_index) in locations.values() if not is_terminal])
                if len(terminals) > 1:
                    self.add_constraint(clues, lambda *values, loc=terminals: check_all_different(values, loc))
                if len(others) > 1:
                    self.add_constraint(clues, lambda *values, loc=others: check_all_different(values, loc))

    def draw_grid(self, location_to_clue_numbers, **args: Any) -> None:
        location_to_clue_numbers = {location: [str((int(value) - 1) % 10 + 1) for value in values]
                                    for location, values in location_to_clue_numbers.items()}
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers, font_multiplier=.8, **args)


if __name__ == '__main__':
    Magpie229.run()
