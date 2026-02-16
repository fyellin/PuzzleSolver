import collections
from operator import itemgetter
from collections.abc import Sequence

import inflect  # type: ignore

from solver import Clue, ClueValue, ClueValueGenerator
from solver import ConstraintSolver
from solver import Evaluator
from solver import Location

eng = inflect.engine()


def create_length_to_integer_dict() -> tuple[dict[tuple[int, int], list[int]], dict[ClueValue, ClueValue]]:
    result: dict[tuple[int, int], list[int]] = collections.defaultdict(list)
    word_sums = dict()
    for i in range(1, 1000):
        clue_value = ClueValue(str(i))
        word = ''.join(i for i in eng.number_to_words(i) if i.islower())
        clue_length = len(clue_value)
        num_letters = len(word)
        word_sums[ClueValue(str(i))] = ClueValue(str(sum(ord(c) - ord('a') + 1 for c in set(word))))
        result[clue_length, num_letters].append(i)
    return result, word_sums


LENGTHS_TO_INTEGERS, WORD_SUMS = create_length_to_integer_dict()


def my_generator(num_letters: int) -> ClueValueGenerator:
    def getter(clue: Clue) -> list[int]:
        return LENGTHS_TO_INTEGERS[clue.length, num_letters]
    return getter


def make(name: str, expression: str, num_letters: int, length: int, base_location: Location) -> 'Clue':
    return Clue(name, name.isupper(), base_location, length,
                context=expression, generator=my_generator(num_letters), expression=expression)


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
    def __init__(self, clue_list: Sequence[Clue]):
        super().__init__(clue_list)
        for clue in clue_list:
            for evaluator in clue.evaluators:
                assert clue.name not in evaluator.vars
                self.__add_constraint_for_clue(clue, evaluator)

    # Note, this method cannot be inlined.  Because clue and evaluator are closed over, they cannot be loop
    # variable in the original code.
    def __add_constraint_for_clue(self, clue: Clue, evaluator: Evaluator) -> None:
        def constraint(arg: ClueValue, *args: ClueValue) -> bool:
            # The args are in the same order as the evaluator.vars, so we can create a Letter->value dictionary
            # by zipping them together.
            evaluator_dictionary = dict(zip(evaluator.vars, map(int, args)))
            return WORD_SUMS[arg] == evaluator(evaluator_dictionary)

        constraint_vars = [clue.name] + list(evaluator.vars)
        self.add_constraint(constraint_vars, constraint, name=f'Clue {clue.name}')

    def show_solution(self, known_clues: dict[Clue, ClueValue]) -> None:
        super().show_solution(known_clues)
        pairs = [(clue.name, int(value)) for clue, value in known_clues.items()]
        max_length = max(len((str(i))) for (_, i) in pairs)
        pairs.sort()
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))


def run() -> None:
    solver = MySolver(CLUES)
    solver.verify_is_180_symmetric()
    solver.solve(debug=True)


if __name__ == '__main__':
    run()
