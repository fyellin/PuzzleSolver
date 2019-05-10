import collections
import itertools
import re
from datetime import datetime
from types import CodeType
from typing import Optional, Tuple, Dict, List, Iterator, NewType, NamedTuple, Set, Sequence, cast, Any, Callable, \
    Pattern

Location = Tuple[int, int]
ClueValue = NewType('ClueValue', str)
Letter = NewType('Letter', str)


LOCATION_TO_CLUE_DICT: Dict[Location, List[Tuple['Clue', int]]] = collections.defaultdict(list)


class Clue(NamedTuple):
    name: str
    expression: str
    length: int
    base_location: Location
    is_across: bool
    compiled_expression: CodeType

    @staticmethod
    def make(name: str, expression: str, length: int, base_location: Location) -> 'Clue':
        expression_to_compile = expression
        if '=' in expression:
            lambda_function = 'lambda x, *y: x if all(z == x for z in y) else -1'
            expression_as_list = expression_to_compile.replace("=", ",")
            expression_to_compile = f'({lambda_function})({expression_as_list})'
        compiled_expression = compile(expression_to_compile, '<string>', 'eval')
        result = Clue(name, expression, length, base_location, name[0] == 'A', compiled_expression)
        for i, location in enumerate(result.locations()):
            LOCATION_TO_CLUE_DICT[location].append((result, i))
        return result

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
    def verify_is_vertically_symmetric() -> None:
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        for clue in CLUES:
            row, column = clue.base_location
            others = {(x, y) for (x, y) in LOCATION_TO_CLUE_DICT[(row, max_column - column)] if
                      x.is_across == clue.is_across}
            assert len(others) == 1
            clue2, index2 = others.pop()
            assert clue2.length == clue.length
            assert index2 == ((clue.length - 1) if clue.is_across else 0)
        for clue1, clue2 in itertools.permutations(CLUES, 2):
            if clue1.name[1:] == clue2.name[1:]:
                assert clue1.base_location == clue2.base_location

    @staticmethod
    def verify_is_180_symmetric() -> None:
        max_row = 1 + max(row for (row, _) in LOCATION_TO_CLUE_DICT.keys())
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        for clue in CLUES:
            row, column = clue.base_location
            # Find the item(s) in the diagonally opposite location of the same type
            others = {(x, y) for (x, y) in LOCATION_TO_CLUE_DICT[(max_row - row, max_column - column)]
                      if x.is_across == clue.is_across}
            # There better be exactly one, and it better have the same length, and its index must be appropriate
            assert len(others) == 1
            clue2, index2 = others.pop()
            assert clue2.length == clue.length
            assert index2 == clue.length - 1


    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


CLUES = (
    Clue.make('A1', '(O*N*E - (O/R + T*O*T*H)*E)*R', 3, (1, 4)),
    Clue.make('A3', 'O*N/E - O*R*(T - W - O)', 3, (2, 4)),
    Clue.make('A5', 'D*E*V*(I + L/(A*N*D))', 3, (3, 4)),
    Clue.make('A7', 'D + E + E + P + S - E - A', 2, (4, 1)),
    Clue.make('A9', '(W**H)*I*C*(H + L + E)*(T + T + E) + (R*I*S + (W - H)*I)*C - H', 5, (4, 3)),
    Clue.make('A11', 'W*A*L + E*S', 2, (4, 8)),
    Clue.make('A13', '(((H + O)/R)*N)**S + (O + F + A + (D + I)*(L**E - M))*M + A', 9, (6, 1)),
    Clue.make('A15', 'E + I - T + H**(E + R) - O - R', 3, (7, 4)),
    Clue.make('A17', 'A*L*T*E*R*(N + A - T + I - V) + E', 3, (8, 4)),
    Clue.make('A18', 'J + O*(I*N - T)', 3, (9, 4)),
    Clue.make('A20', 'C*(H + A) - R*A*(C - T*E*R*S)', 3, (10, 4)),
    Clue.make('A22', '(F*R*E + E*D - O)*M - (O + F) - (C + H + O + I + C - E)', 3, (12, 4)),
    Clue.make('D1', '((C + A + T)*C)**H + 22', 2, (1, 4)),
    Clue.make('D2', 'S + W * I - T + C * H = S*W + I/(T*C) - H', 2, (1, 6)),
    Clue.make('D4', '(S*E*L*E - C)*(T + (I/O)) -  N', 3, (2, 5)),
    Clue.make('D5', '((F*R*E*E + C)/(H/O) - I)*C*E', 4, (3, 4)),
    Clue.make('D6', '(P*R)**E + D + I*(C*A*M - E)*(N + T)', 4, (3, 6)),
    Clue.make('D7', 'A + (L + P + (H + A + C)*(O - D))*E', 3, (4, 1)),
    Clue.make('D8', 'C / H + O*O*(S + E)', 3, (4, 2), ),
    Clue.make('D9', '(P*R*O*A - I*R*E)*S + I*S', 3, (4, 3)),
    Clue.make('D10', '(S + P*(O + T + T))*H*E', 3, (4, 7)),
    Clue.make('D11', '(D*I*F*F*E*R + E - N) / (C*E)', 3, (4, 8)),
    Clue.make('D12', '(T*H*I*S - O)*(R + T*H) - A*T', 3, (4, 9)),
    Clue.make('D14', '(T + V)* S / E + R + I / E + S', 2, (6, 5)),
    Clue.make('D15', 'V*I + (C*E + V)* E*R + S - A', 3, (7, 4)),
    Clue.make('D16', 'O + P + T + (I + O)* N', 3, (7, 6)),
    Clue.make('D19', 'S*(O - R) + T', 2, (9, 5)),
    Clue.make('D20', 'T + H*(E + P*A*I*(R + S))', 3, (10, 4)),
    Clue.make('D21', '(W * (H + I) + C) * H', 3, (10, 6))
)


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
    def make_pattern(clue: Clue, intersections: Sequence['Intersection']) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        temp = ['.'] * (clue.length + 1)
        temp[-1] = '$'
        for index, location in enumerate(clue.locations()):
            if len(LOCATION_TO_CLUE_DICT[location]) > 1:
                temp[index] = '[1-9]'
        if not intersections:
            pattern = re.compile(''.join(temp))
            return lambda x: pattern
        else:
            def getter(known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
                result = temp[:]
                for intersection in intersections:
                    result[intersection.this_index] = known_clues[intersection.other_clue][intersection.other_index]
                return re.compile(''.join(result))
            return getter


class SolvingStep(NamedTuple):
    clue: Clue
    letters: Sequence[Letter]
    pattern: Callable[[Dict[Clue, ClueValue]], Pattern[str]]


DEBUG = False


class Solver:
    count_total: int
    known_letters: Dict[Letter, int]
    known_clues: Dict[Clue, ClueValue]
    solving_steps: Sequence[SolvingStep]

    def __init__(self) -> None:
        self.solving_steps = Solver._get_solving_steps()

    @staticmethod
    def _get_solving_steps() -> Sequence[SolvingStep]:
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Clue, Tuple[Clue, Set[Letter], List[Intersection]]] = {
            clue: (clue, {Letter(ch) for ch in clue.expression if 'A' <= ch <= 'Z'}, [])
            for clue in CLUES
        }

        def evaluator(item: Tuple[Clue, Set[Letter], List[Any]]) -> Sequence[int]:
            clue, unknown_letters, intersections = item
            return -len(unknown_letters), len(intersections), len(intersections) - clue.length

        while not_yet_ordered:
            clue, unknown_letters, intersections = max(not_yet_ordered.values(), key=evaluator)
            not_yet_ordered.pop(clue)
            pattern = Intersection.make_pattern(clue, intersections)
            result.append(SolvingStep(clue, tuple(sorted(unknown_letters)), pattern))
            for (other_clue, other_unknown_letters, other_filled_crossing_clues) in not_yet_ordered.values():
                other_unknown_letters.difference_update(unknown_letters)
                maybe_clash = Intersection.maybe_make(other_clue, clue)
                if maybe_clash:
                    other_filled_crossing_clues.append(maybe_clash)
        return tuple(result)

    def solve(self) -> None:
        self.count_total = 0
        self.known_letters = {}
        self.known_clues = {}
        self.__solve(0)

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_steps):
            self._print_known_letters()
            self._print_board()
            return
        solving_step = self.solving_steps[current_index]
        clue = solving_step.clue
        clue_letters = solving_step.letters
        current_letter_values = tuple(self.known_letters.values())

        pattern = solving_step.pattern(self.known_clues)
        try:
            for next_letter_values in itertools.product(range(1, 10), repeat=len(clue_letters)):
                self.count_total += 1
                if any(current_letter_values.count(value) + next_letter_values.count(value) >= 3
                       for value in next_letter_values):
                    continue
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                value = clue.eval(self.known_letters)
                if not value:
                    continue
                if not pattern.match(value):
                    continue

                def show_it(info: str) -> None:
                    if DEBUG and current_index < 0:
                        print(f'{" | " * current_index} {clue.name} {clue_letters} '
                              f'{next_letter_values} {value} ({clue.length}): {info}')

                self.known_clues[clue] = value
                show_it('--->')
                self.__solve(current_index + 1)
        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            self.known_clues.pop(clue, None)

    def _print_board(self) -> None:
        max_row = 1 + max(row for (row, _) in LOCATION_TO_CLUE_DICT.keys())
        max_column = 1 + max(column for (_, column) in LOCATION_TO_CLUE_DICT.keys())
        board = [[' ' for _ in range(max_column)] for _ in range(max_row)]
        for clue, clue_value in self.known_clues.items():
            for (row, column), letter in zip(clue.locations(), clue_value):
                board[row - 1][column - 1] = letter
        print('\n'.join(''.join(bl) for bl in board))

    def _print_known_letters(self) -> None:
        values: Dict[int, List[Letter]] = collections.defaultdict(list)
        for letter, value in self.known_letters.items():
            values[value].append(letter)
        print(*(i for i in range(1, 10)))
        print(*(values[i][0] for i in range(1, 10)))
        print(*(values[i][1] for i in range(1, 10)))


def run() -> None:
    time1 = datetime.now()
    solver = Solver()
    time2 = datetime.now()
    solver.solve()
    time3 = datetime.now()
    print(solver.count_total, time2 - time1, time3 - time2, time3 - time1)


if __name__ == '__main__':
    Clue.verify_is_vertically_symmetric()
    # import cProfile
    # cProfile.run("Solver.run()")
    run()
