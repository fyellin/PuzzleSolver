import collections
from typing import Tuple, Dict, List, Set, Mapping, FrozenSet

import inflect  # type: ignore

from Clue import Clue, Location, ClueValue, ClueValueGenerator, ClueList, Letter
from GenericSolver import ConstraintSolver

eng = inflect.engine()


LOCATION_TO_CLUE_DICT: Dict[Location, List[Tuple['Clue', int]]] = collections.defaultdict(list)


def create_length_to_integer_dict() -> Tuple[Dict[Tuple[int, int], List[int]], Dict[ClueValue, ClueValue]]:
    result: Dict[Tuple[int, int], List[int]] = collections.defaultdict(list)
    word_sums = dict()
    for i in range(1, 1000):
        clue_value = ClueValue(str(i))
        word = ''.join(i for i in eng.number_to_words(i) if i.islower())
        clue_length = len(clue_value)
        num_letters = len(word)
        word_sums[clue_value] = ClueValue(str(sum(ord(c) - ord('a') + 1 for c in set(word))))
        result[(clue_length, num_letters)].append(i)
    return result, word_sums


LENGTHS_TO_INTEGERS, WORD_SUMS = create_length_to_integer_dict()


def my_generator(num_letters: int) -> ClueValueGenerator:
    def getter(clue: Clue) -> List[int]:
        return LENGTHS_TO_INTEGERS[(clue.length, num_letters)]
    return getter


def make(name: str, expression: str, num_letters: int, length: int, base_location: Location) -> 'Clue':
    return Clue(name, name.isupper(), base_location, length,
                expression=expression, generator=my_generator(num_letters))


CLUES = (
    #     definition        num_letters len x  y
    make('A', 'n',                  6, 2, (1, 1)),
    make('B', 'e',                 16, 3, (1, 3)),
    make('C', 'f + k/A = k + d/A', 23, 3, (2, 1)),
    make('D', 'M - H',             21, 3, (2, 4)),
    make('E', 'f',                 23, 3, (3, 2)),
    make('F', 'k - b',             11, 2, (3, 5)),
    make('G', 'd',                  9, 2, (4, 1)),
    make('H', 'E',                 24, 3, (4, 3)),
    make('K', 'B - b = d + G',     25, 3, (5, 1)),
    make('M', 'G',                 18, 3, (5, 4)),
    make('N', 'B',                 23, 3, (6, 2)),
    make('P', 'c',                 10, 2, (6, 5)),
    make('a', 'C',                 23, 3, (1, 2)),
    make('b', 'A + G',              9, 2, (1, 3)),
    make('c', 'E',                 22, 3, (1, 5)),
    make('d', 'F',                 11, 2, (1, 6)),
    make('e', '(h -  F) / 2',      23, 3, (2, 1)),
    make('f', 'H',                 25, 3, (2, 4)),
    make('g', '(H +  D) / 2',      23, 3, (3, 3)),
    make('h', 'G',                 11, 3, (3, 6)),
    make('k', 'H',                 24, 3, (4, 2)),
    make('m', 'C - b',             22, 3, (4, 5)),
    make('n', 'G',                 10, 2, (5, 1)),
    make('p', 'D',                  9, 2, (5, 4)),
)


class MySolver(ConstraintSolver):
    expression_letters: Dict[Clue, Set[str]]

    def __init__(self, clue_list: ClueList):
        super().__init__(clue_list)
        self.expression_letters = {clue: {x for x in clue.expression if x.isalpha()} for clue in clue_list}

    def post_clue_assignment_fixup(self, clue: Clue, known_clues: Mapping[Clue, ClueValue],
                                   unknown_clues: Dict[Clue, FrozenSet[ClueValue]]) -> bool:
        known_letters = {x.name for x in self.known_clues}
        new_expressions = {clue2 for clue2 in self.clue_list
                           if self.expression_letters[clue2].issubset(known_letters)
                           if clue.name in self.expression_letters[clue2]}
        if new_expressions:
            eval_dict = {Letter(x.name): int(known_clues[x]) for x in known_clues}
            for expression_clue in new_expressions:
                result = expression_clue.eval(eval_dict)
                if not result:
                    return False
                if not self.check_clue_filter(expression_clue, unknown_clues, lambda x: WORD_SUMS[x] == result):
                    return False

        return True


def run() -> None:
    clue_list = ClueList(CLUES)
    clue_list.verify_is_180_symmetric()
    solver = MySolver(clue_list)
    solver.solve()


if __name__ == '__main__':
    run()
