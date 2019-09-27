import itertools
import random
from collections import defaultdict
from datetime import datetime
from typing import Tuple, Dict, List, Sequence, cast, Callable, FrozenSet, Any, Union, Optional, Collection

from mypy_extensions import VarArg

from .base_solver import BaseSolver
from .clue import Clue, ClueValueGenerator
from .clue_list import ClueList
from .clue_types import ClueValue
from .intersection import Intersection

KnownClueDict = Dict[Clue, ClueValue]


class ConstraintSolver(BaseSolver):
    step_count: int
    solution_count: int
    known_clues: KnownClueDict
    debug: bool
    constraints: Dict[Clue, List[Callable[..., bool]]]
    constraint_names: Dict[Callable[..., bool], str]
    all_intersections: Dict[Clue, Sequence[Tuple[Clue, Sequence[Intersection]]]]

    def __init__(self, clue_list: ClueList, **kwargs: Any) -> None:
        super().__init__(clue_list, **kwargs)
        self.constraints = defaultdict(list)
        self.constraint_names = {}
        self.all_intersections = self.__get_all_intersections()

    def add_constraint(self, clues: Sequence[Union[Clue, str]], predicate: Callable[..., bool],
                       *, name: Optional[str] = None) -> None:
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_list.clue_named(clue) for clue in clues)
        if len(actual_clues) == 2:
            clue1, clue2 = actual_clues

            def check_relationship(unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
                return self.__check_2_clue_constraint(clue1, clue2, unknown_clues, predicate)
        else:
            def check_relationship(unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
                return self.__check_n_clue_constraint(actual_clues, unknown_clues, predicate)
        for clue in actual_clues:
            self.constraints[clue].append(check_relationship)
        if not name:
            name = '-'.join(clue.name for clue in actual_clues)
        self.constraint_names[predicate] = name

    def solve(self, *, show_time: bool = True, debug: bool = False) -> int:
        self.step_count = 0
        self.solution_count = 0
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        initial_unknown_clues = {clue: self.__get_initial_values_for_clue(clue)
                                 for clue in self.clue_list if clue.generator}
        time2 = datetime.now()
        self.__solve(initial_unknown_clues)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self.solution_count}; Steps: {self.step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self.solution_count

    def __solve(self, unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> None:
        depth = len(self.known_clues)
        if not unknown_clues:
            if self.check_solution(self.known_clues):
                self.show_solution(self.known_clues)
                self.solution_count += 1
            return
        # find the clue -> values with the smallest possible number of values and the greatest length
        clue, values = min(unknown_clues.items(), key=lambda x: (len(x[1]), -x[0].length, random.random()))
        if not values:
            if self.debug:
                print(f'{" | " * depth}{clue.name} XX')
            return
        constraints = self.constraints[clue]
        seen_values = set(self.known_clues.values())

        try:
            self.step_count += len(values)
            for i, value in enumerate(sorted(values)):
                is_duplicate = not self.allow_duplicates and value in seen_values
                if self.debug:
                    print(f'{" | " * depth}{clue.name} {i + 1}/{len(values)}: {value} --> '
                          f'{"dup" if is_duplicate else ""}')
                if is_duplicate:
                    continue

                self.known_clues[clue] = value
                # Make a shallow copy of unknown_clues, but remove this clue.
                next_unknown_clues = dict(unknown_clues)
                next_unknown_clues.pop(clue)
                # Check the constraints.
                if not all(constraint(next_unknown_clues) for constraint in constraints):
                    continue

                # Look at all the other clues intersecting "clue", and their intersections.
                for clue2, intersections in self.all_intersections[clue]:
                    if clue2 in next_unknown_clues:
                        values2: Collection[ClueValue] = next_unknown_clues[clue2]
                        values2_size = len(values2)
                        for intersection in intersections:
                            values2 = [x for x in values2 if intersection.values_match(value, x)]
                            if self.debug and len(values2) != values2_size:
                                print(f'{"   " * depth}   {clue2.name} {values2_size} -> {len(values2)} '
                                      f'[{intersection}]')
                                values2_size = len(values2)
                        if not values2:
                            break
                        next_unknown_clues[clue2] = frozenset(values2)
                else:
                    # If none of the clues above caused a "break" by going to zero, then we continue.
                    self.__solve(next_unknown_clues)

        finally:
            self.known_clues.pop(clue, None)

    def __get_initial_values_for_clue(self, clue: Clue) -> FrozenSet[ClueValue]:
        """
        Generates all the possible values for the clue, but tosses out those that have a zero in a bad location,
        or otherwise don't find the expected pattern.
        """
        # Generates all the possible values for the clue, but tosses out those that have a zero in a bad location.
        pattern_generator = Intersection.make_pattern_generator(clue, (), self.clue_list)
        pattern = pattern_generator({})
        clue_generator = cast(ClueValueGenerator, clue.generator)  # we know clue_generator isn't None
        string_values = ((str(x) if isinstance(x, int) else x) for x in clue_generator(clue))
        result = frozenset(x for x in string_values if pattern.match(x))
        return cast(FrozenSet[ClueValue], result)

    def __get_all_intersections(self) -> Dict[Clue, Sequence[Tuple[Clue, Sequence[Intersection]]]]:
        """
        For each clue, returns every other clue that it intersects, and the list of those intersections
        """
        result: Dict[Clue, List[Tuple[Clue, Sequence[Intersection]]]] = {clue: [] for clue in self.clue_list}
        for clue, clue2 in itertools.permutations(self.clue_list, 2):
            intersections = Intersection.get_intersections(clue, clue2)
            if intersections:
                result[clue].append((clue2, intersections))
        # mypy isn't happy returning a List when I've declared "sequence"
        return cast(Dict[Clue, Sequence[Tuple[Clue, Sequence[Intersection]]]], result)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        """Overridden by subclasses that need to confirm a solution."""
        return True

    def show_solution(self, known_clues: KnownClueDict) -> None:
        """Overridden by subclasses that want to do more than just show a plot of the board."""
        self.clue_list.plot_board(known_clues)

    def __check_2_clue_constraint(
            self, clue1: Clue, clue2: Clue,
            unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
            clue_filter: Callable[[ClueValue, ClueValue], bool]) -> bool:
        """
        Used by constraints with two variables.
        Ensures that clue1 and clue2 satisfy a certain relationship.
        If the value of both clues is already known, it will make sure that the values pass the relationship.
        If the value of only one clue is known, this will remove all values of the other clue that don't pass the
        relationship.
        """
        value1, value2 = self.known_clues.get(clue1, None), self.known_clues.get(clue2, None)
        unknown_values_count = (value1 is None) + (value2 is None)
        if unknown_values_count == 1:
            if value1:
                unknown_clue = clue2
                start_value = unknown_clues[clue2]
                end_value = unknown_clues[clue2] = frozenset(x for x in start_value if clue_filter(value1, x))
            else:
                unknown_clue = clue1
                start_value = unknown_clues[clue1]
                end_value = unknown_clues[clue1] = frozenset(
                    x for x in start_value if clue_filter(x, cast(ClueValue, value2)))
            if self.debug:
                self.__debug_show_constraint(unknown_clue, clue_filter, start_value, end_value)
            return bool(end_value)
        elif unknown_values_count == 0:
            assert clue_filter(cast(ClueValue, value1), cast(ClueValue, value2))
        return True

    def __check_n_clue_constraint(self, clues: Tuple[Clue, ...],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[[VarArg(ClueValue)], bool]) -> bool:
        """
        Used by constraints with more than two variables.
        Ensures that the clues satisfy a certain relationship.
        If the value of all clues is already known, it will make sure that the values pass the relationship.
        If the value of all but one is known, this will remove all values of the remaining unknown clue that don't
        pass the relationship.
        """
        values = [self.known_clues.get(clue, None) for clue in clues]
        unknown_values_count = values.count(None)

        if unknown_values_count == 1:
            unknown_index = values.index(None)
            unknown_clue = clues[unknown_index]

            def clue_filter_caller(value: ClueValue) -> bool:
                values[unknown_index] = value
                return clue_filter(*cast(List[ClueValue], values))

            start_value = unknown_clues[unknown_clue]
            end_value = unknown_clues[unknown_clue] = frozenset(filter(clue_filter_caller, start_value))
            if self.debug:
                self.__debug_show_constraint(unknown_clue, clue_filter, start_value, end_value)
            return bool(end_value)
        elif unknown_values_count == 0:
            assert clue_filter(*cast(List[ClueValue], values))
        return True

    def __debug_show_constraint(self, clue: Clue, clue_filter: Callable[..., bool],
                                start_value: FrozenSet[ClueValue], end_value: FrozenSet[ClueValue]) -> None:
        if self.debug and len(start_value) != len(end_value):
            depth = len(self.known_clues) - 1
            name = self.constraint_names[clue_filter]
            print(f'{"   " * depth}   {clue.name} {len(start_value)} -> {len(end_value)} [{name}] ')
