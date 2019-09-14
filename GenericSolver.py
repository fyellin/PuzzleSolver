import functools
import itertools
import random
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from typing import Tuple, Dict, List, NamedTuple, Set, Sequence, cast, Callable, \
    Pattern, FrozenSet, Iterable, Any, Union, Optional

from mypy_extensions import VarArg

from Clue import ClueValueGenerator, Clue, ClueValue, Letter, ClueList, Location, Evaluator
from Intersection import Intersection

KnownLetterDict = Dict[Letter, int]
ClueInfo = Tuple[Clue, Evaluator, Set[Letter], List[Intersection], Set[Location]]


class SolvingStep(NamedTuple):
    clue: Clue  # The clue we are solving
    evaluator: Evaluator
    letters: Sequence[Letter]  # The letters we are assigning a value in this step
    pattern_maker: Callable[[Dict[Clue, ClueValue]], Pattern[str]]  # a pattern maker


class BaseSolver(ABC):
    clue_list: ClueList
    allow_duplicates: bool

    def __init__(self, clue_list: ClueList, *, allow_duplicates: bool = False) -> None:
        self.clue_list = clue_list
        self.allow_duplicates = allow_duplicates

    @abstractmethod
    def solve(self, *, show_time: bool = True, debug: bool = False) -> int: ...


class EquationSolver(BaseSolver, ABC):
    step_count: int
    solution_count: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_order: Sequence[SolvingStep]
    items: Sequence[int]
    debug: bool

    def __init__(self, clue_list: ClueList, *, items: Sequence[int] = (), **args: Any) -> None:
        super().__init__(clue_list, **args)
        self.items = items

    def solve(self, *, show_time: bool = True, debug: bool = False) -> int:
        self.step_count = 0
        self.solution_count = 0
        self.known_letters = {}
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        self.solving_order = self._get_solving_order()
        time2 = datetime.now()
        self.__solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self.solution_count}; steps: {self.step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self.solution_count

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_order):
            if self.check_solution(self.known_clues, self.known_letters):
                self.show_solution(self.known_clues, self.known_letters)
                self.solution_count += 1
            return
        clue, evaluator, clue_letters, pattern_maker = self.solving_order[current_index]
        is_twin = clue in self.known_clues
        pattern = pattern_maker(self.known_clues)
        if self.debug:
            print(f'{" | " * current_index} {clue.name} length={clue_letters} pattern="{pattern.pattern}"')

        try:
            for next_letter_values in self.get_letter_values(self.known_letters, len(clue_letters)):
                self.step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                clue_value = evaluator(self.known_letters)
                if is_twin:
                    if clue_value != self.known_clues[clue]:
                        continue
                else:
                    if not (clue_value and pattern.match(clue_value)):
                        continue
                    if not self.allow_duplicates and clue_value in self.known_clues.values():
                        continue
                    self.known_clues[clue] = clue_value

                if self.debug:
                    print(f'{" | " * current_index} {clue.name} {clue_letters} '
                          f'{next_letter_values} {clue_value} ({clue.length}): -->')

                self.__solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            if not is_twin:
                self.known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Any, ClueInfo] = {
            # co_names are the unbound variables in the compiled expression: exactly what we want!
            evaluator: (clue, evaluator, set(evaluator.vars), [], set())
            for clue in self.clue_list for evaluator in clue.evaluators
        }

        def grading_function(clue_info: ClueInfo) -> Sequence[float]:
            (clue, _, unknown_letters, _, locations) = clue_info
            return -len(unknown_letters), len(locations) / clue.length, clue.length

        while not_yet_ordered:
            clue, evaluator, unknown_letters, intersections, _ = max(not_yet_ordered.values(), key=grading_function)
            not_yet_ordered.pop(evaluator)
            pattern = Intersection.make_pattern_generator(clue, intersections, self.clue_list)
            result.append(SolvingStep(clue, evaluator, tuple(sorted(unknown_letters)), pattern))
            for (other_clue, _, other_unknown_letters, other_intersections, other_locations) in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                new_intersections = Intersection.get_intersections(other_clue, clue)
                other_intersections += new_intersections
                other_locations.update(intersection.get_location() for intersection in new_intersections)

        return tuple(result)

    def get_letter_values(self, known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        if count == 0:
            yield ()
            return
        unused_values = (i for i in self.items if i not in set(known_letters.values()))
        yield from itertools.permutations(unused_values, count)

    def get_letter_values_with_duplicates(self, known_letters: Dict[Letter, int], count: int, max_per_item: int) -> \
            Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = tuple(known_letters.values())
        for next_letter_values in itertools.product(self.items, repeat=count):
            if all(current_letter_values.count(value) + next_letter_values.count(value) <= max_per_item
                   for value in next_letter_values):
                yield next_letter_values

    def check_solution(self, _known_clues: Dict[Clue, ClueValue], _known_letters: Dict[Letter, int]) -> bool:
        """
        Called when we have a tentative solution.  You should override this method if additional checking
        is required.

        :param _known_clues: A dictionary giving the value of each of the clues.  Clue -> ClueValue
        :param _known_letters: A dictionary giving the value of each equation letter.  Letter -> int
        :return: True if this solution is correct; false otherwise
        """
        return True

    def show_solution(self, known_clues: Dict[Clue, ClueValue], known_letters: Dict[Letter, int]) -> None:
        self.clue_list.plot_board(known_clues)
        max_length = max(len(str(i)) for i in known_letters.values())
        print()
        pairs = [(letter, value) for letter, value in known_letters.items()]
        pairs.sort()
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))


class ConstraintSolver(BaseSolver):
    step_count: int
    solution_count: int
    known_clues: Dict[Clue, ClueValue]
    debug: bool
    constraints: Dict[Clue, List[Callable[..., bool]]]
    constraint_names: Dict[Callable[..., bool], str]

    def __init__(self, clue_list: ClueList, **kwargs: Any) -> None:
        self.constraints = defaultdict(list)
        self.constraint_names = {}
        super().__init__(clue_list)

    def add_constraint(self, clues: Sequence[Union[Clue, str]], predicate: Callable[..., bool],
                       *, name: Optional[str] = None) -> None:
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_list.clue_named(clue) for clue in clues)
        if len(actual_clues) == 2:
            clue1, clue2 = actual_clues

            def check_relationship(unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
                return self.check_2_clue_relationship(clue1, clue2, unknown_clues, predicate)
        else:
            def check_relationship(unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
                return self.check_n_clue_relationship(actual_clues, unknown_clues, predicate)
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
        initial_unknown_clues = {clue: self.__get_all_possible_values(clue)
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

        try:
            self.step_count += len(values)
            for i, value in enumerate(sorted(values)):
                if self.debug:
                    print(f'{" | " * depth}{clue.name} {i + 1}/{len(values)}: {value} -->')
                self.known_clues[clue] = value
                next_unknown_clues = dict(unknown_clues)
                next_unknown_clues.pop(clue)
                if not all(constraint(next_unknown_clues) for constraint in constraints):
                    continue
                for clue2, values2 in next_unknown_clues.items():
                    intersections = self.__get_insersections(clue2, clue)
                    if intersections:
                        temp = list(values2) if self.allow_duplicates else [x for x in values2 if x != value]
                        for intersection in intersections:
                            temp = [x for x in temp if intersection.values_match(x, value)]
                        result = frozenset(temp)
                    elif self.allow_duplicates or value not in values2:
                        result = values2
                    else:
                        result = values2 - {value}

                    if self.debug and result != values2:
                        print(f'{"   " * depth}   {clue2.name} {len(values2)} -> {len(result)}')
                    next_unknown_clues[clue2] = result
                    if not result:
                        break
                else:
                    # If none of the clues above caused a "break" from going to zero, then we continue.
                    self.__solve(next_unknown_clues)

        finally:
            self.known_clues.pop(clue, None)

    def __get_all_possible_values(self, clue: Clue) -> FrozenSet[ClueValue]:
        # Generates all the possible values for the clue, but tosses out those that have a zero in a bad location.
        pattern_generator = Intersection.make_pattern_generator(clue, (), self.clue_list)
        pattern = pattern_generator({})
        clue_generator = cast(ClueValueGenerator, clue.generator)  # we know clue_generator isn't None
        string_values = ((str(x) if isinstance(x, int) else x) for x in clue_generator(clue))
        result = frozenset(x for x in string_values if pattern.match(x))
        return cast(FrozenSet[ClueValue], result)

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def __get_insersections(this: Clue, other: Clue) -> Sequence[Intersection]:
        return Intersection.get_intersections(this, other)

    def check_solution(self, known_clues: Dict[Clue, ClueValue]) -> bool:
        return True

    def show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        self.clue_list.plot_board(known_clues)

    def check_2_clue_relationship(
            self, clue1: Clue, clue2: Clue,
            unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
            clue_filter: Callable[[ClueValue, ClueValue], bool]) -> bool:
        """
        Intended to be called from an override of post_clue_assignment_fixup.
        Ensures that clue1 and clue2 satisfy a certain relationship.
        If the value of both clues is already known, it will make sure that the values pass the relationship.
        If the value of only one clue is known, the will remove all possible values of the unknown clue
        that don't pass the relationship.
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

    def check_n_clue_relationship(self, clues: Tuple[Clue, ...],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[[VarArg(ClueValue)], bool]) -> bool:
        """
        Intended to be called from an override of post_clue_assignment_fixup.
        Ensures that the values of the clues satisfy a certain relationship.
        If the values of all clues is already known, it will make sure that the values pass the relationship.
        If the value of all but one clue is known, the will remove all possible values of the unknown clue
        that don't pass the relationship.
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


