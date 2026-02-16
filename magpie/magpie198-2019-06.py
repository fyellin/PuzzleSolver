import collections
import itertools
from enum import Enum
from collections.abc import Iterable, Sequence

from solver import Clue, ClueValueGenerator, KnownClueDict, Location, ClueValue, \
    ConstraintSolver
from solver import generators


class AnswerType(Enum):
    Fibonacci = 1
    Square = 2
    Triangle = 3
    Prime = 4
    Palindrome = 5


def create_to_type_dict() -> dict[str, AnswerType]:
    # Creates a map from legal entry values to the answer type of that entry.  Values are only allowed to belong
    # to one type.
    creator: tuple[tuple[AnswerType, ClueValueGenerator], ...] = (
        (AnswerType.Fibonacci, generators.fibonacci),
        (AnswerType.Square, generators.square),
        (AnswerType.Triangle, generators.triangular),
        (AnswerType.Prime, generators.prime),
        (AnswerType.Palindrome, generators.palindrome))
    items = [(length, answer_type, str(value))
             for length in (1, 2, 3) for answer_type, generator in creator
             for value in generator(Clue('fake', True, (1, 1), length))]
    # count the number of times each value appears in the list of items.
    counter = collections.Counter(value for _, _, value in items)
    # create a map from the value to the type of the value, for those values that are a member
    # of only one group.
    return {value: answer_type for (_, answer_type, value) in items if counter[value] == 1}


TO_TYPE_DICT = create_to_type_dict()


def make(name: str, base_location: Location, length: int, generator: ClueValueGenerator | None) -> Clue:
    return Clue(name, name[0] == 'A', base_location, length, generator=generator)


def normal(clue: Clue) -> Iterable[str]:
    return (x for x in TO_TYPE_DICT if len(x) == clue.length)


def across_10(clue: Clue) -> Iterable[str]:
    return filter(lambda answer: answer[0] > answer[1] > answer[2], normal(clue))


def down_4(clue: Clue) -> Iterable[str]:
    for answer in normal(clue):
        digit_sum = sum(map(int, answer))
        digit_sum_type = TO_TYPE_DICT.get(str(digit_sum), None)
        if digit_sum_type and TO_TYPE_DICT[answer] != digit_sum_type:
            yield answer


def down_8(clue: Clue) -> Iterable[int]:
    return filter(lambda x: str(x) in TO_TYPE_DICT, generators.square(clue))


CLUES = (
    make('A1',  (1, 1), 3, normal),
    make('A3',  (1, 4), 2, normal),
    make('A5',  (2, 1), 2, normal),
    make('A7',  (2, 3), 3, normal),
    make('A10', (3, 2), 3, across_10),
    make('A11', (4, 1), 3, normal),
    make('A13', (4, 4), 2, normal),
    make('A15', (5, 1), 2, normal),
    make('A16', (5, 3), 3, normal),

    make('D1',  (1, 1), 2, normal),
    make('D2',  (1, 3), 2, normal),
    make('D4',  (1, 5), 3, down_4),
    make('D6',  (2, 2), 3, normal),
    make('D8',  (2, 4), 3, down_8),
    make('D9',  (3, 1), 3, normal),
    make('D12', (4, 3), 2, normal),
    make('D14', (4, 5), 2, normal),
)


class MySolver(ConstraintSolver):
    def __init__(self, clue_list: Sequence[Clue]):
        super().__init__(clue_list)
        #  sqrt(d8) is a divisor of a16,, which is the same as d8 being a divisor of a16**2
        self.add_constraint(('D8', 'A16'), lambda d8, a16: int(a16) ** 2 % int(d8) == 0)

        for clue1, clue2 in itertools.combinations(clue_list, 2):
            if clue1.is_across == clue2.is_across:
                match_index = 0 if clue1.is_across else 1
                if clue1.base_location[match_index] == clue2.base_location[match_index]:
                    self.add_constraint((clue1, clue2), lambda x, y: TO_TYPE_DICT[x] == TO_TYPE_DICT[y])
                else:
                    self.add_constraint((clue1, clue2), lambda x, y: TO_TYPE_DICT[x] != TO_TYPE_DICT[y])

    def show_solution(self, known_clues: KnownClueDict) -> None:
        super().show_solution(known_clues)
        for clue in self._clue_list:
            value = known_clues[clue]
            print(f'{clue.name:<3} {value:>3} {TO_TYPE_DICT[value].name}')


def run() -> None:
    solver = MySolver(CLUES)
    solver.verify_is_180_symmetric()
    solver.solve(debug=False)


if __name__ == '__main__':
    run()
