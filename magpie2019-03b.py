import itertools
import re
from collections import Counter
from datetime import datetime
from operator import itemgetter
from types import CodeType
from typing import Optional, Tuple, Dict, List, Iterator, NewType, NamedTuple, Set, Sequence, cast, Any, Callable, \
    Pattern, FrozenSet


DEBUG = False


Location = Tuple[int, int]
ClueValue = NewType('ClueValue', str)
Letter = NewType('Letter', str)


class Clue(NamedTuple):
    name: str
    is_across: bool
    base_location: Location
    length: int
    expression: str
    compiled_expression: CodeType

    @staticmethod
    def make(name: str, is_across: bool, base_location: Location, length: int, expression: str = '0') -> 'Clue':
        expression_to_compile = Clue.__fixup_for_compilation(expression)
        if '=' in expression:
            lambda_function = 'lambda x, *y: x if all(z == x for z in y) else -1'
            expression_as_list = expression_to_compile.replace("=", ",")
            expression_to_compile = f'({lambda_function})({expression_as_list})'
        compiled_expression = compile(expression_to_compile, f'<Clue {name}>', 'eval')
        return Clue(name, is_across, base_location, length, expression, compiled_expression)

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
        expression = expression.replace("^", "**")  # Magpie use a strange minus signo
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


class ClueList:
    clues: Sequence[Clue]
    max_row: int
    max_column: int
    start_locations: FrozenSet[Location]
    intersections: FrozenSet[Location]

    def __init__(self, clues: Sequence[Clue]):
        self.clues = clues
        final_locations: List[Location] = []
        start_locations: Set[Location] = set()
        all_locations = Counter()
        for clue in clues:
            final_locations.append(clue.location(clue.length - 1))
            start_locations.add(clue.base_location)
            all_locations.update(clue.locations())
        self.start_locations = frozenset(start_locations)
        self.intersections = frozenset(location for location, count in all_locations.items() if count >= 2)
        self.max_row = 1 + max(row for (row, _) in final_locations)
        self.max_column = 1 + max(column for (_, column) in final_locations)

    def __iter__(self) -> Iterator[Clue]:
        return iter(self.clues)

    @staticmethod
    def make_clue_list(across: str, down: str, locations: Sequence[Tuple[int, int]]) -> 'ClueList':
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
        return ClueList(result)

    def print_board(self, clue_values: Dict[Clue, ClueValue]) -> None:
        board = [[' ' for _ in range(self.max_column)] for _ in range(self.max_row)]
        for clue, clue_value in clue_values.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))

    def verify_is_vertically_symmetric(self) -> None:
        clue_start_set = self.__make_clue_start_set()
        for clue in self.clues:
            # The location in this clue that matches the start of its mirror opposite
            row, column = clue.location(clue.length - 1 if clue.is_across else 0)
            # The presumed start location of its mirror opposite
            row2, column2 = row, self.max_column - column
            assert ((row2, column2), clue.length, clue.is_across) in clue_start_set

    def verify_is_180_symmetric(self) -> None:
        clue_start_set = self.__make_clue_start_set()
        for clue in self.clues:
            # The location in this clue that matches the start of its symmetric opposite
            row, column = clue.location(clue.length - 1)
            # The presumed start location of its symmetric opposite
            row2, column2 = self.max_column - row, self.max_column - column
            assert ((row2, column2), clue.length, clue.is_across) in clue_start_set

    def verify_is_four_fold_symmetric(self) -> None:
        # for each clue, we make sure the next one clockwise is also there.
        assert self.max_row == self.max_column
        clue_start_set = self.__make_clue_start_set()
        for clue in self.clues:
            # The location in this clue that matches the start of its 90° clockwise rotation
            row, column = clue.location(0 if clue.is_across else clue.length - 1)
            # The presumed start location of the clue located 90° clockwise.
            row2, column2 = column, self.max_column - row
            # Note that across clues rotate to down clues, and vice versa.
            assert ((row2, column2), clue.length, not clue.is_across) in clue_start_set

    def __make_clue_start_set(self) -> Set[Tuple[Location, int, bool]]:
        return {(clue.base_location, clue.length, clue.is_across) for clue in self.clues}


class Intersection(NamedTuple):
    this_index: int
    other_clue: Clue
    other_index: int

    @staticmethod
    def maybe_make(this: Clue, other: Clue) -> Optional['Intersection']:
        if this.is_across == other.is_across:
            return None
        this_row, this_column = this.base_location
        other_row, other_column = other.base_location
        row_delta, column_delta = other_row - this_row, other_column - this_column
        # if "this" is an across clue, the clash is at (this_row, other_column).
        # if "this" is a down clue, the class is at (this_column, other_row).
        my_index, other_index = (column_delta, -row_delta) if this.is_across else (row_delta, -column_delta)
        if 0 <= my_index < this.length and 0 <= other_index < other.length:
            return Intersection(my_index, other, other_index)
        return None

    def values_match(self, this_value: ClueValue, known_clues: Dict[Clue, ClueValue]) -> bool:
        return this_value[self.this_index] == known_clues[self.other_clue][self.other_index]

    @staticmethod
    def make_pattern_generator(clue: Clue, intersections: Sequence['Intersection'], clue_list: ClueList) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        pattern_list = ['[1-9]' if location in clue_list.intersections else '.' for location in clue.locations()]
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


class Solver:
    clue_list: ClueList
    count_total: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_steps: Sequence[SolvingStep]

    def __init__(self, clue_list: ClueList) -> None:
        self.clue_list = clue_list
        self.solving_steps = Solver._get_solving_steps(clue_list)

    @staticmethod
    def _get_solving_steps(clue_list: ClueList) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Clue, Tuple[Clue, Set[Letter], List[Intersection]]] = {
            clue: (clue, {Letter(ch) for ch in clue.expression if 'A' <= ch <= 'Z'}, [])
            for clue in clue_list
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
            pattern = Intersection.make_pattern_generator(clue, intersections, clue_list)
            result.append(SolvingStep(clue, tuple(sorted(unknown_letters)), pattern))
            for (other_clue, other_unknown_letters, other_intersections) in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                maybe_clash = Intersection.maybe_make(other_clue, clue)
                if maybe_clash:
                    other_intersections.append(maybe_clash)
        return tuple(result)

    def solve(self) -> None:
        self.count_total = 0
        self.known_letters = {}
        self.known_clues = {}
        self.__solve(0)

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_steps):
            self._print_known_letters()
            self.clue_list.print_board(self.known_clues)
            return
        solving_step = self.solving_steps[current_index]
        clue = solving_step.clue
        clue_letters = solving_step.letters
        current_letter_values = list(self.known_letters.values())
        pattern = solving_step.pattern_maker(self.known_clues)
        try:
            for next_letter_values in itertools.product(range(1, 10), repeat=len(clue_letters)):
                if any(current_letter_values.count(value) + next_letter_values.count(value) >= 3
                       for value in next_letter_values):
                    continue

                self.count_total += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                clue_value = clue.eval(self.known_letters)
                if not (clue_value and pattern.match(clue_value)):
                    continue

                def show_it(info: str) -> None:
                    if DEBUG:
                        print(f'{" | " * current_index} {clue.name} {clue_letters} '
                              f'{next_letter_values} {clue_value} ({clue.length}): {info}')

                self.known_clues[clue] = clue_value
                show_it('--->')
                self.__solve(current_index + 1)
        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            self.known_clues.pop(clue, None)

    def _print_known_letters(self) -> None:
        pairs = [(letter, value) for letter, value in self.known_letters.items()]
        pairs.sort()
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))
        pairs.sort(key=itemgetter(1))
        print(''.join(f'{letter:<3}' for letter, _ in pairs))
        print(''.join(f'{value:<3}' for _, value in pairs))





# noinspection SpellCheckingInspection
ACROSS = """
1 (ONE – (O/R + TOTH)E)R (3)
3 ON/E – OR(T – W – O) (3)
5 DEV(I + L/(AND)) (3)
7 D + E + E + P + S – E – A (2)
9 (W^H)IC(H + L + E)(T + T + E) + (RIS + (W – H)I)C – H (5)
11 WAL + ES (2)
13 (((H + O)/R)N)^S + (O + F + A + (D + I)(L^E – M))M + A (9)
15 E + I – T + H^(E + R) – O – R (3)
17 ALTER(N + A – T + I – V) + E (3)
18 J + O(IN – T) (3)
20 C(H + A) – RA(C – TERS) (3)
22 (FRE + ED – O)M – (O + F) – (C + H + O + I + C – E) (3)
"""


# noinspection SpellCheckingInspection
DOWN = """
1 ((C + A + T)C)^H + 22 (2)
2 S + WI – T + CH = SW + I/(TC) – H (2)
4 (SELE – C)(T + (I/O)) – N (3)
5 ((FREE + C)/(H/O) – I)CE (4)
6 (PR)^E + D + I(CAM – E)(N + T) (4)
7 A + (L + P + (H + A + C)(O – D))E (3)
8 C/H + OO(S + E) (3)
9 (PROA – IRE)S + IS (3)
10 (S + P(O + T + T))HE (3)
11 (DIFFER + E – N)/(CE) (3)
12 (THIS – O)(R + TH) – AT (3)
14 (T + V)S/E + R + I/E + S (2)
15 VI + (CE + V)ER + S – A (3)
16 O + P + T + (I + O)N (3)
19 S(O – R) + T (2)
20 T + H(E + PAI(R + S)) (3)
21 (W(H + I) + C)H (3)
"""

LOCATIONS: Sequence[Location] = (
    (1, 4), (1, 6), (2, 4), (2, 5), (3, 4), (3, 6),
    (4, 1), (4, 2), (4, 3), (4, 7), (4, 8), (4, 9),
    (6, 1), (6, 5), (7, 4), (7, 6), (8, 4),
    (9, 4), (9, 5), (10, 4), (10, 6), (12, 4))


def run() -> None:
    clue_list = ClueList.make_clue_list(ACROSS, DOWN, LOCATIONS)
    clue_list.verify_is_vertically_symmetric()
    if True:
        time1 = datetime.now()
        solver = Solver(clue_list)
        time2 = datetime.now()
        solver.solve()
        time3 = datetime.now()
        print(solver.count_total, time2 - time1, time3 - time2, time3 - time1)


if __name__ == '__main__':
    run()
