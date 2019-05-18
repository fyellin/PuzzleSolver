import random
from datetime import datetime
import re
from abc import ABC, abstractmethod
from collections import Counter, OrderedDict
from operator import itemgetter
from types import CodeType
import typing
from typing import Optional, Tuple, Dict, List, Iterator, NewType, NamedTuple, Set, Sequence, cast, Any, Callable, \
    Pattern, FrozenSet, Iterable, Union, Mapping

Location = Tuple[int, int]
ClueValue = NewType('ClueValue', str)
Letter = NewType('Letter', str)

ClueValueGenerator = Callable[['Clue'], Iterable[Union[str, int]]]


class Clue(NamedTuple):
    name: str
    is_across: bool
    base_location: Location
    length: int
    expression: str
    compiled_expression: CodeType
    generator: Optional[ClueValueGenerator]

    @staticmethod
    def make(name: str, is_across: bool, base_location: Location, length: int,
             expression: str = '0',
             generator: Optional[ClueValueGenerator] = None) -> 'Clue':
        expression_to_compile = Clue.__fixup_for_compilation(expression)
        if '=' in expression:
            lambda_function = 'lambda x, *y: x if all(z == x for z in y) else -1'
            expression_as_list = expression_to_compile.replace("=", ",")
            expression_to_compile = f'({lambda_function})({expression_as_list})'
        compiled_expression = compile(expression_to_compile, f'<Clue {name}>', 'eval')

        return Clue(name, is_across, base_location, length, expression, compiled_expression, generator)

    def locations(self) -> Iterator[Location]:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        for i in range(self.length):
            yield row + i * row_delta, column + i * column_delta

    def location(self, i: int) -> Location:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        return row + i * row_delta, column + i * column_delta

    def eval(self, known_letters: Dict[Letter, int]) -> Optional[ClueValue]:
        value = eval(self.compiled_expression, None, cast(Any, known_letters))
        if int(value) != value:
            return None
        value = int(value)
        if value < 1:
            return None
        return ClueValue(str(value))

    @staticmethod
    def __fixup_for_compilation(expression: str) -> str:
        """Convert a magpie expression into a Python expression"""
        expression = expression.replace("–", "-")  # Magpie use a strange minus sign
        expression = expression.replace("^", "**")  # Magpie use a strange minus sign
        for _ in range(2):
            # ), letter, or digit followed by (, letter, or digit needs an * in between, except when we have
            # two digits in a row with no space between them.  Note negative lookahead below.
            expression = re.sub(r'(?!\d\d)([\w)])\s*([(\w])', r'\1*\2', expression)
        return expression

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


class ClueList(NamedTuple):
    name_to_clue: Mapping[str, Clue]
    max_row: int
    max_column: int
    # The set of all start locations
    start_locations: FrozenSet[Location]
    # The set of all locations at which two clues intersect
    intersections: FrozenSet[Location]

    @staticmethod
    def create(clues: Sequence[Clue]) -> 'ClueList':
        all_locations: typing.Counter[Location] = Counter(location for clue in clues for location in clue.locations())
        return ClueList(
            name_to_clue=OrderedDict((clue.name, clue) for clue in clues),
            max_row=1 + max(row for (row, _) in all_locations),
            max_column=1 + max(column for (_, column) in all_locations),
            start_locations=frozenset(clue.base_location for clue in clues),
            intersections=frozenset(location for location, count in all_locations.items() if count >= 2))

    @staticmethod
    def create_from_text(across: str, down: str, locations: Sequence[Tuple[int, int]]) -> 'ClueList':
        result: List[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                clue = Clue.make(f'{number}{letter}', is_across, location, int(match.group(3)), match.group(2))
                result.append(clue)
        return ClueList.create(result)

    def get_board(self, clue_values: Dict[Clue, ClueValue]) -> List[List[int]]:
        """Print the board, based on the values for each of the clues"""
        board = [[0 for _ in range(self.max_column - 1)] for _ in range(self.max_row - 1)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = int(letter)
        return board

    def print_board(self, clue_values: Dict[Clue, ClueValue]) -> None:
        """Print the board, based on the values for each of the clues"""
        board = [[' ' for _ in range(self.max_column)] for _ in range(self.max_row)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))

    def clue_named(self, name: str) -> Clue:
        """Returns the new with the specified name"""
        return self.name_to_clue[name]

    def iterator(self) -> Iterator[Clue]:
        return iter(self.name_to_clue.values())

    def verify_is_vertically_symmetric(self) -> None:
        """Verify that the puzzle has vertical symmetry"""
        clue_start_set = self.__make_clue_start_set()
        for clue in self.iterator():
            # The location in this clue that matches the start of its mirror opposite
            row, column = clue.location(clue.length - 1 if clue.is_across else 0)
            # The presumed start location of its mirror opposite
            row2, column2 = row, self.max_column - column
            assert ((row2, column2), clue.length, clue.is_across) in clue_start_set

    def verify_is_180_symmetric(self) -> None:
        """Verify that the puzzle has 180° symmetry"""
        clue_start_set = self.__make_clue_start_set()
        for clue in self.iterator():
            # The location in this clue that matches the start of its symmetric opposite
            row, column = clue.location(clue.length - 1)
            # The presumed start location of its symmetric opposite
            row2, column2 = self.max_column - row, self.max_column - column
            assert ((row2, column2), clue.length, clue.is_across) in clue_start_set

    def verify_is_four_fold_symmetric(self) -> None:
        """Verify that the puzzle has four-fold symmetry"""
        # for each clue, we make sure the next one clockwise is also there.
        assert self.max_row == self.max_column
        clue_start_set = self.__make_clue_start_set()
        for clue in self.iterator():
            # The location in this clue that matches the start of its 90° clockwise rotation
            row, column = clue.location(0 if clue.is_across else clue.length - 1)
            # The presumed start location of the clue located 90° clockwise.
            row2, column2 = column, self.max_column - row
            # Note that across clues rotate to down clues, and vice versa.
            assert ((row2, column2), clue.length, not clue.is_across) in clue_start_set

    def __make_clue_start_set(self) -> Set[Tuple[Location, int, bool]]:
        """Creates the set of (start-location, length, is-across) tuples for all clues in the puzzle"""
        return {(clue.base_location, clue.length, clue.is_across) for clue in self.name_to_clue.values()}


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

    def values_match(self, this_value: ClueValue, known_clues: Dict[Clue, ClueValue]) -> bool:
        return this_value[self.this_index] == known_clues[self.other_clue][self.other_index]

    @staticmethod
    def make_pattern_generator(clue: Clue, intersections: Sequence['Intersection'],
                               solver: Union['SolverByLetter', 'SolverByClue']) -> \
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
            args = (known_clues[intersection.other_clue][intersection.other_index] for intersection in intersections)
            regexp = pattern_format.format(*args)
            return re.compile(regexp)

        return getter


class SolvingStep(NamedTuple):
    clue: Clue  # The clue we are solving
    letters: Sequence[Letter]  # The letters we are assigning a value
    pattern_maker: Callable[[Dict[Clue, ClueValue]], Pattern[str]]  # a pattern maker


class SolverByLetter(ABC):
    clue_list: ClueList
    count_total: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_order: Sequence[SolvingStep]
    debug: bool

    def __init__(self, clue_list: ClueList) -> None:
        self.clue_list = clue_list

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
            self.show_solution(self.known_letters)
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
            for clue in self.clue_list.iterator()
        }

        def evaluator(item: Tuple[Clue, Set[Letter], List[Intersection]]) -> Sequence[int]:
            # Largest value wins.  Precedence is given to the clue with the least number of unknown variables.
            # Within that, ties are broken by the one with the most number of intersecting clues.
            # Within that, ties are broken by the longest clue length, so we create the most intersections
            clue, unknown_letters, intersections = item
            return -len(unknown_letters), len(intersections), clue.length

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
        raise Exception()

    def get_allowed_regexp(self, location: Location) -> str:
        return '.' if self.is_zero_allowed(location) else '[1-9]'

    def is_zero_allowed(self, location: Location) -> bool:
        """Returns true if a 0 is allowed at this clue location.  Overrideable by subclasses"""
        return location not in self.clue_list.start_locations

    def show_solution(self, known_letters: Dict[Letter, int]) -> None:
        self.clue_list.print_board(self.known_clues)
        print()
        pairs = [(letter, value) for letter, value in known_letters.items()]
        pairs.sort()
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))


class SolverByClue:
    clue_list: ClueList
    count_total: int
    known_clues: Dict[Clue, ClueValue]
    debug: bool

    def __init__(self, clue_list: ClueList) -> None:
        self.clue_list = clue_list

    def solve(self, *, show_time: bool = True, debug: bool = False) -> None:
        self.count_total = 0
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        initial_unknown_clues = {clue: self.__get_all_possible_values(clue)
                      for clue in self.clue_list.iterator() if clue.generator}
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
                if not self.post_assignment_cleanup(clue, self.known_clues, next_unknown_clues):
                    if self.debug:
                        print(f'{" | " * depth}   {clue.name} External check failed.')
                    continue
                for clue2, values2 in next_unknown_clues.items():
                    intersection = Intersection.maybe_make(clue2, clue)
                    if intersection:
                        result = frozenset(
                            x for x in values2 if x != value and intersection.values_match(x, self.known_clues))
                    else:
                        result = values2 - {value}
                    if self.debug and result != values2:
                        print(f'{"   " * depth}   {clue2.name} {len(values2)} -> {len(result)}')
                    next_unknown_clues[clue2] = result
                self.__solve(next_unknown_clues)

        finally:
            self.known_clues.pop(clue, None)

    def __get_all_possible_values(self, clue: Clue) -> FrozenSet[ClueValue]:
        # Generates all the possible values for the clue, but tosses out those that have a zero in a bad location.
        pattern_generator = Intersection.make_pattern_generator(clue, (), self)
        pattern = pattern_generator({})
        clue_generator = cast(ClueValueGenerator, clue.generator)  # we know clue_generator isn't None
        return frozenset(ClueValue(x) for x in map(str, clue_generator(clue)) if pattern.match(x))

    def get_allowed_regexp(self, location: Location) -> str:
        """
        Allows the user to be specific about which characters are allowed at a specific location.  The default is
        just to use is_zero_allowed(), and base the decision on what that returns.
        """

        return '.' if self.is_zero_allowed(location) else '[1-9]'

    def is_zero_allowed(self, location: Location) -> bool:
        """Indicates whether a zero is allowed at a specific location by the rules of the puzzle.  The default is
        not to allow a zero at the start of a clue.  Solvers can override this, or they can instead implement
        get_allowed_regexp() which allows even finer control.
        """
        return location not in self.clue_list.start_locations

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        self.clue_list.print_board(known_clues)

    def post_assignment_cleanup(self, clue: Clue, known_clues: Dict[Clue, ClueValue],
                                unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
        """
        Allows the user to make solver-specific modifications to the list of clues and their not-yet-known values.
        This can be used to add a new clue (for example, one clue is a cube of another) or to modify the values of an
        already existing clue.  You can even add a clue with no possible values to indicate a failure.
        """
        return True
