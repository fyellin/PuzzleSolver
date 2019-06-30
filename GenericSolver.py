import itertools
import random
import re
from abc import ABC, abstractmethod
from datetime import datetime
from operator import itemgetter
from typing import Optional, Tuple, Dict, List, NamedTuple, Set, Sequence, cast, Callable, \
    Pattern, FrozenSet, Iterable, Mapping, overload

from Clue import Location, ClueValueGenerator, Clue, ClueValue, Letter, ClueList


class Intersection(NamedTuple):
    this_index: int
    other_clue: Clue
    other_index: int

    @staticmethod
    def maybe_make(this: Clue, other: Clue) -> Optional['Intersection']:
        """If this clue and the other clue have an intersection, return it.  Otherwise return None."""
        if this.is_across == other.is_across:
            return None
        this_row, this_column = this.base_location
        other_row, other_column = other.base_location
        # if "this" is an across clue, the intersection is at (this_row, other_column).
        # if "this" is a down clue, the intersection is at (this_column, other_row).
        row_delta, column_delta = other_row - this_row, other_column - this_column
        my_index, other_index = (column_delta, -row_delta) if this.is_across else (row_delta, -column_delta)
        # if both indices are within bounds, we have an intersection.
        if 0 <= my_index < this.length and 0 <= other_index < other.length:
            return Intersection(my_index, other, other_index)
        return None

    def values_match(self, this_value: ClueValue, other_value: ClueValue) -> bool:
        return this_value[self.this_index] == other_value[self.other_index]

    @staticmethod
    def make_pattern_generator(clue: Clue, intersections: Sequence['Intersection'],
                               solver: 'BaseSolver') -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        pattern_list = [solver.get_allowed_regexp(location) for location in clue.locations()]
        pattern_list.append('$')

        if not intersections:
            pattern = re.compile(''.join(pattern_list))
            return lambda _: pattern

        # {0}, {1}, etc represent the order the items appear in the  "intersections" argument, not necessarily
        # the order that they appear in the pattern.  format can handle that.
        for i, intersection in enumerate(intersections):
            pattern_list[intersection.this_index] = f'{{{i}:s}}'
        pattern_format = ''.join(pattern_list)

        def getter(known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
            args = (known_clues[x.other_clue][x.other_index] for x in intersections)
            regexp = pattern_format.format(*args)
            return re.compile(regexp)

        return getter

    @staticmethod
    def make_runtime_pattern(clue: Clue, known_clues: Dict[Clue, ClueValue],
                             solver: 'BaseSolver') -> Pattern[str]:
        pattern_list = [solver.get_allowed_regexp(location) for location in clue.locations()]
        pattern_list.append('$')
        for other_clue, other_clue_value in known_clues.items():
            intersection = Intersection.maybe_make(clue, other_clue)
            if intersection:
                pattern_list[intersection.this_index] = other_clue_value[intersection.other_index]
        return re.compile(''.join(pattern_list))


class SolvingStep(NamedTuple):
    clue: Clue  # The clue we are solving
    letters: Sequence[Letter]  # The letters we are assigning a value in this step
    pattern_maker: Callable[[Dict[Clue, ClueValue]], Pattern[str]]  # a pattern maker


class BaseSolver(ABC):
    clue_list: ClueList

    def __init__(self, clue_list: ClueList) -> None:
        self.clue_list = clue_list

    @abstractmethod
    def solve(self, *, show_time: bool = True, debug: bool = False) -> None: ...

    def get_allowed_regexp(self, location: Location) -> str:
        return '.' if self.is_zero_allowed(location) else '[^0]'

    def is_zero_allowed(self, location: Location) -> bool:
        """Returns true if a 0 is allowed at this clue location.  Overrideable by subclasses"""
        return not self.clue_list.is_start_location(location)


class SolverByLetter(BaseSolver, ABC):
    count_total: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_order: Sequence[SolvingStep]
    debug: bool

    def __init__(self, clue_list: ClueList) -> None:
        super(SolverByLetter, self).__init__(clue_list)

    def solve(self, *, show_time: bool = True, debug: bool = False) -> None:
        self.count_total = 0
        self.known_letters = {}
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        self.solving_order = self._get_solving_order()
        time2 = datetime.now()
        self.__solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Steps: {self.count_total}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_order):
            self.check_and_show_solution(self.known_letters)
            return
        solving_step = self.solving_order[current_index]
        clue = solving_step.clue
        clue_letters = solving_step.letters
        pattern = solving_step.pattern_maker(self.known_clues)
        try:
            for next_letter_values in self.get_letter_values(self.known_letters, len(clue_letters)):
                self.count_total += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                clue_value = clue.eval(self.known_letters)
                if not (clue_value and pattern.match(clue_value)):
                    continue

                def show_it(info: str) -> None:
                    if self.debug:
                        print(f'{" | " * current_index} {clue.name} {clue_letters} '
                              f'{next_letter_values} {clue_value} ({clue.length}): {info}')

                self.known_clues[clue] = clue_value
                show_it('--->')
                self.__solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            self.known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Clue, Tuple[Clue, Set[Letter], List[Intersection]]] = {
            clue: (clue, {Letter(ch) for ch in clue.expression if 'A' <= ch <= 'Z'}, [])
            for clue in self.clue_list
        }

        def evaluator(item: Tuple[Clue, Set[Letter], List[Intersection]]) -> Sequence[int]:
            # Largest value wins.  Precedence is given to the clue with the least number of unknown variables.
            # Within that, ties are broken by the one with the most number of intersecting clues.
            # Within that, ties are broken by the longest clue length, so we create the most intersections
            clue, clue_unknown_letters, clue_intersections = item
            return -len(clue_unknown_letters), len(clue_intersections), clue.length

        while not_yet_ordered:
            clue, unknown_letters, intersections = max(not_yet_ordered.values(), key=evaluator)
            not_yet_ordered.pop(clue)
            pattern = Intersection.make_pattern_generator(clue, intersections, self)
            result.append(SolvingStep(clue, tuple(sorted(unknown_letters)), pattern))
            for (other_clue, other_unknown_letters, other_intersections) in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                maybe_clash = Intersection.maybe_make(other_clue, clue)
                if maybe_clash:
                    other_intersections.append(maybe_clash)
        return tuple(result)

    @abstractmethod
    def get_letter_values(self, known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        raise Exception()

    @staticmethod
    def get_letter_values_impl(minimum: int, maximum: int, known_letters: Dict[Letter, int], count: int) -> \
            Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = set(known_letters.values())
        for next_letter_values in itertools.permutations(range(minimum, maximum + 1), count):
            if all(v not in current_letter_values for v in next_letter_values):
                yield next_letter_values

    @staticmethod
    def get_letter_values_n_impl(minimum: int, maximum: int, max_count: int,
                                 known_letters: Dict[Letter, int], count: int) -> Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = tuple(known_letters.values())
        for next_letter_values in itertools.product(range(minimum, maximum + 1), repeat=count):
            if all(current_letter_values.count(value) + next_letter_values.count(value) <= max_count
                   for value in next_letter_values):
                yield next_letter_values

    def check_and_show_solution(self, known_letters: Dict[Letter, int]) -> None:
        self.clue_list.plot_board(self.known_clues)
        print()
        pairs = [(letter, value) for letter, value in known_letters.items()]
        pairs.sort()
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))


class SolverByClue(BaseSolver):
    count_total: int
    known_clues: Dict[Clue, ClueValue]
    allow_duplicates: bool
    debug: bool

    def __init__(self, clue_list: ClueList, allow_duplicates: bool = False) -> None:
        super(SolverByClue, self).__init__(clue_list)
        self.allow_duplicates = allow_duplicates

    def solve(self, *, show_time: bool = True, debug: bool = False) -> None:
        self.count_total = 0
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        initial_unknown_clues = {clue: self.__get_all_possible_values(clue)
                                 for clue in self.clue_list if clue.generator}
        time2 = datetime.now()
        self.__solve(initial_unknown_clues)
        time3 = datetime.now()
        if show_time:
            print(f'Steps: {self.count_total}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')

    def __solve(self, unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> None:
        depth = len(self.known_clues)
        if not unknown_clues:
            self.check_and_show_solution(self.known_clues)
            return
        # find the clue -> values with the smallest possible number of values
        clue, values = min(unknown_clues.items(), key=lambda x: (len(x[1]), x[0].length, random.random()))
        if not values:
            if self.debug:
                print(f'{" | " * depth}{clue.name} XX')
            return

        try:
            self.count_total += len(values)
            for i, value in enumerate(sorted(values)):
                if self.debug:
                    print(f'{" | " * depth}{clue.name} {i + 1}/{len(values)}: {value} -->')
                self.known_clues[clue] = value
                next_unknown_clues = dict(unknown_clues)
                next_unknown_clues.pop(clue)
                if not self.post_clue_assignment_fixup(clue, self.known_clues, next_unknown_clues):
                    continue
                for clue2, values2 in next_unknown_clues.items():
                    intersection = self.maybe_make_intersection(clue2, clue)
                    if intersection:
                        result = frozenset(
                            x for x in values2 if x != value and intersection.values_match(x, value))
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


    def maybe_make_intersection(self, clue1: Clue, clue2: Clue) -> Optional[Intersection]:
        "Pulled out into a separate method so that it can be overridden."
        return Intersection.maybe_make(clue1, clue2)


    def __get_all_possible_values(self, clue: Clue) -> FrozenSet[ClueValue]:
        # Generates all the possible values for the clue, but tosses out those that have a zero in a bad location.
        pattern_generator = Intersection.make_pattern_generator(clue, (), self)
        pattern = pattern_generator({})
        clue_generator = cast(ClueValueGenerator, clue.generator)  # we know clue_generator isn't None
        return frozenset(ClueValue(x) for x in map(str, clue_generator(clue)) if pattern.match(x))

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        self.clue_list.plot_board(known_clues)

    def post_clue_assignment_fixup(self, clue: Clue, known_clues: Mapping[Clue, ClueValue],
                                   unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
        """
        Allows the user to make solver-specific modifications to the list of clues and their not-yet-known values.
        This can be used to add a new clue (for example, one clue is a cube of another) or to modify the values of an
        already existing clue.  You can even add a clue with no possible values to indicate a failure.
        """
        return True

    def check_clue_filter(self, clue: Clue, unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                          clue_filter: Callable[[ClueValue], bool]) -> bool:
        """
        Intended to be called from an override of post_clue_assignment_fixup.
        Ensures that the value of a clue passes a certain filter.  If the value of the clue is already
        known, it will make sure that the value passes the filter.  If the value of the clue is not
        already known, it will remove all possible values that don't pass the filter
        """
        value = self.known_clues.get(clue, None)
        if value:
            return clue_filter(value)
        else:
            start_value = unknown_clues[clue]
            end_value = unknown_clues[clue] = frozenset(x for x in start_value if clue_filter(x))
            if self.debug and len(start_value) != len(end_value):
                depth = len(self.known_clues) - 1
                print(f'{"   " * depth}   [1] {clue.name} {len(start_value)} -> {len(end_value)}')
            return bool(end_value)

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
            if self.debug and len(start_value) != len(end_value):
                depth = len(self.known_clues) - 1
                print(f'{"   " * depth}   [2] {unknown_clue.name} {len(start_value)} -> {len(end_value)}')
            return bool(end_value)
        elif unknown_values_count == 0:
            result = clue_filter(cast(ClueValue, value1), cast(ClueValue, value2))
            if not result and self.debug:
                depth = len(self.known_clues) - 1
                print(f'{"   " * depth}   [2] {clue1.name}={value1} {clue2.name}={value2} -> XXX')
            return result
        else:
            return True

    @overload
    def check_n_clue_relationship(self, clues: Tuple[Clue, Clue],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[[ClueValue, ClueValue], bool]) -> bool:
        ...

    @overload
    def check_n_clue_relationship(self, clues: Tuple[Clue, Clue, Clue],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[[ClueValue, ClueValue, ClueValue], bool]) -> bool:
        ...

    @overload
    def check_n_clue_relationship(self, clues: Tuple[Clue, Clue, Clue, Clue],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[[ClueValue, ClueValue, ClueValue, ClueValue], bool]) -> bool:
        ...

    def check_n_clue_relationship(self, clues: Sequence[Clue],
                                  unknown_clues: Dict[Clue, FrozenSet[ClueValue]],
                                  clue_filter: Callable[..., bool]) -> bool:
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
            prefix = cast(List[ClueValue], values[:unknown_index])
            suffix = cast(List[ClueValue], values[unknown_index + 1:])
            start_value = unknown_clues[unknown_clue]
            end_value = unknown_clues[unknown_clue] = frozenset(
                x for x in start_value if clue_filter(*prefix, x, *suffix))
            if self.debug and len(start_value) != len(end_value):
                depth = len(self.known_clues) - 1
                print(f'{"   " * depth}   [r] {unknown_clue.name} {len(start_value)} -> {len(end_value)}')
            return bool(end_value)
        elif unknown_values_count == 0:
            return clue_filter(*cast(List[ClueValue], values))
        else:
            return True
