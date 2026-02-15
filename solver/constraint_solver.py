from __future__ import annotations

import abc
import itertools
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime
from heapq import nlargest, nsmallest
from typing import Any, NamedTuple, Protocol, cast

from .base_solver import BaseSolver, KnownClueDict
from .clue import Clue, ClueValueGenerator
from .clue_types import ClueValue
from .intersection import Intersection

type UnknownClueDict = dict[Clue, Sequence[ClueValue]]


class ConstraintSolver(BaseSolver):
    _step_count: int
    _solution_count: int
    _known_clues: KnownClueDict
    _debug: bool
    _start_clues: Sequence[Clue]
    _max_debug_depth: int
    _multi_constraints: dict[Clue, list[Callable[..., bool]]]
    _singleton_constraint: dict[Clue, list[Callable[..., bool]]]
    _letter_handler: AbstractLetterCountHandler | None

    def __init__(self, clue_list: Sequence[Clue], constraints: Sequence[Constraint] = (),
                 *, letter_handler: AbstractLetterCountHandler | None = None,
                 **kwargs: Any) -> None:
        super().__init__(clue_list, **kwargs)
        self._multi_constraints = defaultdict(list)
        self._singleton_constraint = defaultdict(list)
        self._letter_handler = letter_handler

        for clue, clue2 in itertools.permutations(self._clue_list, 2):
            for intersection in Intersection.get_intersections(clue, clue2):
                self.__add_intersection_constraint(clue, clue2, intersection)

        for constraint in constraints:
            clues, predicate, name = constraint
            self.add_constraint(clues, predicate, name=name)

    def add_constraint(self, clues: Sequence[Clue | str] | str,
                       predicate: Callable[..., bool],
                       *, name: str | None = None) -> None:
        if isinstance(clues, str):
            clues = clues.split()
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_named(clue)
                             for clue in clues)
        actual_name = name or '-'.join(clue.name for clue in actual_clues)

        if len(actual_clues) == 1:
            self._singleton_constraint[actual_clues[0]].append(predicate)
            return

        if len(actual_clues) == 2:
            # This is just an optimization, since the two-clue case in the most common
            clue1, clue2 = actual_clues

            def check_relationship(unknown_clues: UnknownClueDict) -> bool:
                return self.__check_2_clue_constraint(clue1, clue2, unknown_clues,
                                                      predicate, actual_name)
        else:
            def check_relationship(unknown_clues: UnknownClueDict) -> bool:
                return self.__check_n_clue_constraint(actual_clues, unknown_clues,
                                                      predicate, actual_name)
        for clue in actual_clues:
            self._multi_constraints[clue].append(check_relationship)

    def add_extended_constraint(self, clues: Sequence[Clue | str],
                                predicate: Callable[..., Sequence[ClueValue]],
                                *, name: str | None = None) -> None:
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_named(clue)
                             for clue in clues)
        actual_name = name or '-'.join(clue.name for clue in actual_clues)
        assert len(clues) > 1

        def check_relationship(unknown_clues: UnknownClueDict) -> bool:
            return self.__check_extended_constraint(actual_clues, unknown_clues,
                                                    predicate, actual_name)

        for clue in actual_clues:
            self._multi_constraints[clue].append(check_relationship)

    def __add_intersection_constraint(self, this_clue: Clue, other_clue: Clue,
                                      intersection: Intersection):
        name = str(intersection)
        this_index, other_index = intersection.this_index, intersection.other_index

        def check_relationship(unknown_clues: UnknownClueDict) -> bool:
            if other_clue not in unknown_clues:
                return True
            char = self._known_clues[this_clue][this_index]
            start_value = unknown_clues[other_clue]
            end_value = [value for value in start_value if char == value[other_index]]
            if len(self._known_clues) < self._max_debug_depth:
                self.__debug_show_constraint(other_clue, name, start_value, end_value)
            unknown_clues[other_clue] = end_value
            return bool(end_value)

        self._multi_constraints[this_clue].append(check_relationship)

    def solve(self, *, show_time: bool = True, debug: bool = False,
              max_debug_depth: int | None = None,
              start_clues: Sequence[Clue | str] = ()) -> int:
        self._step_count = 0
        self._solution_count = 0
        self._known_clues = {}
        self._debug = debug
        self._start_clues = [self.clue_named(x) if isinstance(x, str) else x
                             for x in start_clues]
        self._max_debug_depth = -1 if not debug else (max_debug_depth or 1000)
        time1 = datetime.now()
        initial_unknown_clues = {clue: self.__get_initial_values_for_clue(clue)
                                 for clue in self._clue_list if clue.generator}
        self._letter_handler and self._letter_handler.start()
        time2 = datetime.now()
        self.__solve(initial_unknown_clues)
        self._letter_handler and self._letter_handler.close()
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self._solution_count}; Steps: {self._step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; '
                  f'Total: {time3 - time1}')
        return self._solution_count

    def __solve(self, unknown_clues: UnknownClueDict) -> None:
        depth = len(self._known_clues)
        if not unknown_clues:
            if self.check_solution(self._known_clues):
                self._solution_count += 1
                self.show_solution(self._known_clues)
                if depth < self._max_debug_depth:
                    print(f'{"***" * depth}***SOLVED***"')
            return

        if depth < len(self._start_clues):
            clue = self._start_clues[depth]
            values = unknown_clues[clue]
        else:
            # find the clue -> values with the smallest possible number of values
            # and the greatest length
            clue, values = min(unknown_clues.items(),
                               key=lambda x: (len(x[1]), -x[0].length, x[0].name))
        if not values:
            if depth < self._max_debug_depth:
                print(f'{" | " * depth}{clue.name} XX')
            return
        constraints = self._multi_constraints[clue]
        seen_values = set(self._known_clues.values())
        letter_handler = self._letter_handler

        try:
            lh_clue_info = letter_handler and letter_handler.get_clue_info(clue)
            for i, value in enumerate(values):
                self._step_count += 1
                is_duplicate = (not self._allow_duplicates and value in seen_values
                                and len(value) > 1)
                fails_letter_handler = letter_handler and \
                    not letter_handler.checking_value(value, lh_clue_info)
                if depth < self._max_debug_depth:
                    print(f'{" | " * depth}{clue.name} {i + 1}/{len(values)}: '
                          f'{value.__repr__()} -->'
                          f'{" dup" if is_duplicate else ""}'
                          f'{" letter-handling-fail" if fails_letter_handler else ""}'
                          f' [{self._step_count}]')
                if is_duplicate or fails_letter_handler:
                    continue

                self._known_clues[clue] = value
                # Make a shallow copy of unknown_clues, but remove this clue.
                next_unknown_clues = dict(unknown_clues)
                del next_unknown_clues[clue]
                # Check the constraints.
                if not all(constraint(next_unknown_clues) for constraint in constraints):
                    continue
                if letter_handler:
                    letter_handler.adding_value(value, lh_clue_info)
                self.__solve(next_unknown_clues)
                if letter_handler:
                    letter_handler.removing_value(value, lh_clue_info)

        finally:
            self._known_clues.pop(clue, None)

    def get_initial_values_for_clue(self, clue):
        return self.__get_initial_values_for_clue(clue)

    def __get_initial_values_for_clue(self, clue: Clue) -> Sequence[ClueValue]:
        """
        Generates all the possible values for the clue, but tosses out those that have a
        zero in a bad location, or otherwise don't find the expected pattern.
        """
        pattern_generator = Intersection.make_pattern_generator(clue, (), self)
        pattern = pattern_generator({})
        clue_generator = cast(ClueValueGenerator, clue.generator)
        string_values = [(str(x) if isinstance(x, int) else x)
                         for x in clue_generator(clue)]
        predicates = self._singleton_constraint[clue]
        result = sorted([x for x in string_values
                         if pattern.fullmatch(x)
                         if all(predicate(x) for predicate in predicates)])
        if self._max_debug_depth > 0:
            def show_full(x):
                return [item.__repr__() for item in x]

            if len(result) <= 20:
                print(f'{clue.name}: ({", ".join(show_full(result))})')
            else:
                smallest = nsmallest(8, result)
                largest = nlargest(8, result)
                largest.reverse()
                print(f'{clue.name}: ({", ".join(show_full(smallest))} '
                      f'[{len(result) - 16} skipped] {", ".join(show_full(largest))})')
        return cast(Sequence[ClueValue], result)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        return True

    def show_solution(self, known_clues: KnownClueDict) -> None:
        """Overridden by subclasses that want to do more than show a plot."""
        self.plot_board(known_clues)

    def __check_2_clue_constraint(
            self, clue1: Clue, clue2: Clue,
            unknown_clues: UnknownClueDict,
            clue_filter: Callable[[ClueValue, ClueValue], bool],
            name: str) -> bool:
        """
        Used by constraints with two variables.
        Ensures that clue1 and clue2 satisfy a certain relationship.
        If the value of only one clue is known, this will remove all values of
        the other clue that don't pass the relationship.
        """
        value1 = self._known_clues.get(clue1, None)
        value2 = self._known_clues.get(clue2, None)
        unknown_values_count = (value1 is None) + (value2 is None)
        if unknown_values_count == 1:
            if value1 is not None:
                unknown_clue = clue2
                start_value = unknown_clues[clue2]
                end_value = unknown_clues[clue2] = [
                    x for x in start_value if clue_filter(value1, x)]
            else:
                unknown_clue = clue1
                start_value = unknown_clues[clue1]
                end_value = unknown_clues[clue1] = [
                    x for x in start_value if clue_filter(x, cast(ClueValue, value2))]
            if len(self._known_clues) < self._max_debug_depth:
                self.__debug_show_constraint(unknown_clue, name, start_value, end_value)
            return bool(end_value)
        return True

    def __check_n_clue_constraint(self, clues: tuple[Clue, ...],
                                  unknown_clues: UnknownClueDict,
                                  clue_filter: Callable[..., bool],
                                  name: str) -> bool:
        """
        Used by constraints with more than two variables.
        Ensures that the clues satisfy a certain relationship.
        If the value of all but one is known, this will remove all values of
        the remaining unknown clue that don't pass the relationship.
        """
        values = [self._known_clues.get(clue, None) for clue in clues]
        unknown_values_count = values.count(None)

        if unknown_values_count == 1:
            unknown_index = values.index(None)
            unknown_clue = clues[unknown_index]
            pre_values, post_values = values[:unknown_index], values[unknown_index + 1:]

            start_value = unknown_clues[unknown_clue]
            end_value = unknown_clues[unknown_clue] = [
                value for value in start_value
                if clue_filter(*pre_values, value, *post_values)]
            if len(self._known_clues) < self._max_debug_depth:
                self.__debug_show_constraint(unknown_clue, name, start_value, end_value)
            return bool(end_value)
        return True

    def __check_extended_constraint(self, clues: tuple[Clue, ...],
                                    unknown_clues: UnknownClueDict,
                                    clue_filter: Callable[..., Sequence[ClueValue]],
                                    name: str) -> bool:
        values = [self._known_clues.get(clue, None) for clue in clues]
        unknown_values_count = values.count(None)

        if unknown_values_count != 1:
            return True

        unknown_index = values.index(None)
        unknown_clue = clues[unknown_index]

        start_value = unknown_clues[unknown_clue]
        end_value = unknown_clues[unknown_clue] = list(clue_filter(start_value, *values))

        if len(self._known_clues) < self._max_debug_depth:
            self.__debug_show_constraint(unknown_clue, name, start_value, end_value)
        return bool(end_value)

    def __debug_show_constraint(self, clue: Clue, constraint_name: str,
                                start_value: Sequence[ClueValue],
                                end_value: Sequence[ClueValue]) -> None:
        if len(start_value) != len(end_value):
            depth = len(self._known_clues) - 1
            print(f'{"   " * depth}   {clue.name} {len(start_value)} -> '
                  f'{len(end_value)} [{constraint_name}] ')


class Constraint(NamedTuple):
    clues: Sequence[Clue | str] | str
    predicate: Callable[..., bool]
    name: str | None = None


type LCH_Info = tuple[Sequence[int], set[tuple[int, int]]]


class AbstractLetterCountHandler(Protocol):
    def start(self) -> None: ...
    def get_clue_info(self, clue: Clue) -> Any: ...
    def checking_value(self, value: ClueValue, info: Any) -> bool: ...
    def adding_value(self, value: ClueValue, info: Any) -> None: ...
    def removing_value(self, value: ClueValue, info: Any) -> None: ...
    def close(self) -> None: ...


class LetterCountHandler(AbstractLetterCountHandler):
    _locations: set[tuple[int, int]]
    _counter: Counter[str]

    @abc.abstractmethod
    def real_checking_value(self, value: ClueValue, info: Any) -> bool:
        ...

    def start(self):
        self._locations = set()
        self._counter = Counter()

    def get_clue_info(self, clue: Clue) -> LCH_Info:
        temp = [(index, location) for index, location in enumerate(clue.locations)
                if location not in self._locations]
        new_locations = {location for _, location in temp}
        new_indices = [index for index, _ in temp]
        return new_indices, new_locations

    def checking_value(self, value: ClueValue, info: LCH_Info) -> bool:
        counter = self._counter
        indices, _locations = info
        counter.update(value[index] for index in indices)
        result = self.real_checking_value(value, info)
        counter.subtract(value[index] for index in indices)
        return result

    def adding_value(self, value: ClueValue, info: LCH_Info) -> None:
        indices, locations = info
        self._counter.update(value[index] for index in indices)
        self._locations |= locations

    def removing_value(self, value: ClueValue, info: LCH_Info) -> None:
        indices, locations = info
        self._counter.subtract(value[index] for index in indices)
        self._locations -= locations

    def close(self) -> None:
        assert len(self._locations) == 0
        assert all(x == 0 for x in self._counter.values())
