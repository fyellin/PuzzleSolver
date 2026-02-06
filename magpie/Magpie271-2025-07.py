import itertools
import math
import time
from collections import defaultdict
from typing import Sequence

from solver import ClueValue, Clues, EquationSolver, Evaluator, Letter

CLUES = """
A TH(E + T) + A
B E + T/A
B (I/O)TA
C M + U
C (OM − IC)(RO − N)
D B(E + T)A
G ((O + M)E + G)/A
H RH − O
I (L + A)(MBD + A)
K A((L + P)/H + A)
K S(I + G) − M + A
L D − E(L − T)A
M CH + I
N (U − P)S + I(LO + N)
O P − H + I
O P + I
P (T/A)U
P X + I
R K(A + PP)/A
S Z(E + T)A
T (P − S)I
U (GA + M)M − A
X NU
Z (EP + S)I + L − O − N
"""

ACROSS_LENGTHS = "33/42/24/42/24/33"
DOWN_LENGTHS = "222/141/33/33/141/222"


# Look at Magpie 256 when we're done

class Magpie256(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solver()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        self.clue_by_number = defaultdict(list)
        for clue in clues:
            self.clue_by_number[int(clue.name[:-1])].append(clue)
        self.double_numbers = {key for key, value in self.clue_by_number.items()
                               if len(value) == 2}
        self.not_double_numbers = {key for key, value in self.clue_by_number.items()
                                   if len(value) == 1}
        super().__init__(clues)
        self.expressions = self.parse_expressions()
        self.double_letters = {key1 for (key1, _), (key2, _) in
                               itertools.pairwise(self.expressions) if key1 == key2}

    def parse_expressions(self) -> Sequence[tuple[Letter, Evaluator]]:
        return [(Letter(key), evaluator)
                for line in CLUES.strip().splitlines()
                for key in [line[0]]
                for evaluator in [Evaluator.create_evaluator(line[1:].strip())]]

    def solver(self, debug=False):
        known_letters = value_is_used = board = steps = solutions = None

        def start(runner):
            nonlocal known_letters, value_is_used, board, steps, solutions
            steps = solutions = 0
            known_letters = {}
            value_is_used = [False] * 21
            board = {}
            runner()

        def get_value_for_var(letter, allowed_values, next_function, next_args):
            nonlocal steps
            for value in allowed_values:
                if not value_is_used[value]:
                    steps += 1
                    value_is_used[value] = True
                    known_letters[letter] = value
                    next_function(*next_args)
                    value_is_used[value] = False

        def debug_show_assignment(prefix, letters, this_letter, evaluator, next_function, next_args):
            if debug:
                info = ' '.join(f'{this_letter}={known_letters[letter]} // {letter} = {evaluator}' for letter in letters)
                print(prefix, info)
            next_function(*next_args)

        def add_to_board(letter, evaluator, prefix, next_function, next_args):
            result = evaluator.raw_call(known_letters)
            if result < 10 or result > 9999 or int(result) != result:
                return
            result = int(result)
            clues = self.clue_by_number[known_letters[letter]]
            for clue in clues:
                if len(string_result := str(result)) == clue.length:
                    locations_set = []
                    for location, char in zip(clue.locations, string_result):
                        if (old_char := board.get(location)) is not None:
                            if char != old_char:
                                if debug:
                                    print(prefix, f'{result}@{clue.name} clash at {location}')
                                break
                        else:
                            if char == '0' and self.is_start_location(location):
                                if debug:
                                    print(prefix, f'{result}@{clue.name} bad 0 at {location}')
                                break
                            board[location] = char
                            locations_set.append(location)
                    else:
                        # We end up here if we never performed a "break".
                        if debug:
                            print(prefix, f'{result}@{clue.name} works fine!')
                        next_function(*next_args)
                    for location in locations_set:
                        del board[location]
                else:
                    if debug:
                        print(prefix, f'{result}@{clue.name} is wrong length')

        def print_result(_next_function, _next_args):
            nonlocal solutions
            solutions += 1
            known_clues = {
                clue: ClueValue(''.join(board[location] for location in clue.locations))
                for clue in self._clue_list}
            self.show_solution(known_clues, known_letters)
            for key, expression in self.expressions:
                print(f'{key}={known_letters[key]:2}: '
                      f'{int(expression.raw_call(known_letters)):4} // {expression}')

        def get_runner(expressions):
            steps = []
            known_vars = set()
            for depth, (letter, evaluator) in enumerate(expressions):
                unknown_vars = [var for var in evaluator.vars if var not in known_vars]
                if not (letter in known_vars or letter in unknown_vars):
                    unknown_vars.append(letter)
                known_vars.update(unknown_vars)
                for var in unknown_vars:
                    allowed = ((20,) if var == 'E' else self.double_numbers
                        if var in self.double_letters else self.not_double_numbers)
                    steps.append((get_value_for_var, (var, allowed)))
                steps.append((debug_show_assignment, (' | ' * depth, unknown_vars, letter, evaluator)))
                steps.append((add_to_board, (letter, evaluator, '   ' * depth)))
            steps.append((print_result, ()))

            current_function, current_args = (lambda *x: None), None
            for (func, args) in reversed(steps):
                current_args = (*args, current_function, current_args)
                current_function = func
            return lambda: current_function(*current_args)

        evaluation_order = self.get_evaluation_order()
        runner = get_runner(evaluation_order)
        start_time = time.perf_counter_ns()
        start(runner)
        end_time = time.perf_counter_ns()
        print(f'{(end_time - start_time) / 1_000_000}ms; {steps} steps')

    def get_evaluation_order(self) -> list[tuple[tuple[Letter, bool], Evaluator]]:
        result = []
        expressions = list(self.expressions)
        seen = set()

        def cost(item):
            _index, (key, evaluator) = item
            variables = (set(evaluator.vars) | {key}) - seen
            total = math.prod(
                1 if var == 'E' else 5 if var in self.double_letters else 10
                for var in variables)
            return total

        while expressions:
            # We can't just sort because each time we update "seen" which changes the
            # cost function
            index, (key, evaluator) = min(enumerate(expressions), key=cost)
            expressions.pop(index)
            result.append((key, evaluator))
            seen.update(evaluator.vars)
            seen.add(key)
        return result


if __name__ == '__main__':
    Magpie256.run()
    # Magpie256Alt.run()
