import collections
from enum import Enum
from typing import Iterable, Optional, Dict, FrozenSet, Mapping, Tuple

import Generators
from GenericSolver import SolverByClue
from Clue import Location, ClueValueGenerator, Clue, ClueValue, ClueList


class AnswerType(Enum):
    Fibonacci = 1
    Square = 2
    Triangle = 3
    Prime = 4
    Palindrome = 5


def create_to_type_dict() -> Dict[str, AnswerType]:
    # Creates a map from legal entry values to the answer type of that entry.  Values are only allowed to belong
    # to one type.
    creator: Tuple[Tuple[AnswerType, ClueValueGenerator], ...] = (
        (AnswerType.Fibonacci, Generators.fibonacci),
        (AnswerType.Square, Generators.square),
        (AnswerType.Triangle, Generators.triangular),
        (AnswerType.Prime, Generators.prime),
        (AnswerType.Palindrome, Generators.palindrome))
    items = [(length, answer_type, str(value))
             for length in (1, 2, 3) for answer_type, generator in creator
             for value in generator(Clue('fake', True, (1, 1), length))]
    # count the number of times each value appears in the list of items.
    counter = collections.Counter(value for _, _, value in items)
    # create a map from the value to the type of the value, for those values that are a member
    # of only one group.
    return {value: answer_type for (_, answer_type, value) in items if counter[value] == 1}


TO_TYPE_DICT = create_to_type_dict()


def make(name: str, base_location: Location, length: int, generator: Optional[ClueValueGenerator]) -> Clue:
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
    return filter(lambda x: str(x) in TO_TYPE_DICT, Generators.square(clue))


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


class MySolver(SolverByClue):
    def __init__(self, clue_list: ClueList):
        self.d8 = clue_list.clue_named('D8')
        self.a16 = clue_list.clue_named('A16')
        super(MySolver, self).__init__(clue_list)

    def post_clue_assignment_fixup(self, clue: Clue, known_clues: Mapping[Clue, ClueValue],
                                   unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
        # When we set the value of a clue, we indicate that whatever AnswerType that value has is exclusive to that
        # row or column.  All clues in that row or column must have the same AnswerType, and all clues in the other
        # rows/column must have a different answer type.
        this_answer = known_clues[clue]
        this_type = TO_TYPE_DICT[this_answer]
        this_location = clue.base_location
        match_index = 0 if clue.is_across else 1
        for other_clue in self.clue_list:
            # iterate over all the other clues that are similarly across/down, and that haven't been solved yet.
            if other_clue == clue or other_clue.is_across != clue.is_across or other_clue not in unknown_clues:
                continue
            other_location = other_clue.base_location
            is_row_column_match = this_location[match_index] == other_location[match_index]

            def keep_value(value: ClueValue) -> bool:
                types_match = (this_type == TO_TYPE_DICT[value])
                # If this is the same row/column, the types must match.  Otherwise, they must differ
                return is_row_column_match == types_match
            start_value = unknown_clues[other_clue]
            unknown_clues[other_clue] = end_value = frozenset(filter(keep_value, start_value))
            if self.debug and len(start_value) != len(end_value):
                depth = len(self.known_clues) - 1
                print(f'{"   " * depth}   [P] {other_clue.name} {len(start_value)} -> {len(end_value)}')

            if not end_value:
                return False

        if clue == self.d8 or clue == self.a16:
            #  sqrt(d8) is a divisor of a16,, which is the same as d8 being a divisor of a16**2
            return self.check_2_clue_relationship(self.d8, self.a16, unknown_clues,
                                                  lambda d8, a16: int(a16) ** 2 % int(d8) == 0)

        return True

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        super().check_and_show_solution(known_clues)
        for clue in self.clue_list:
            value = known_clues[clue]
            print(f'{clue.name:<3} {value:>3} {TO_TYPE_DICT[value].name}')
        self.clue_list.plot_board(known_clues)


def run() -> None:
    clue_list = ClueList(CLUES)
    clue_list.verify_is_180_symmetric()
    solver = MySolver(clue_list)
    solver.solve(debug=False)


if __name__ == '__main__':
    run()
