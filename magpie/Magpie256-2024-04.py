import itertools
import time
from typing import Any, Sequence, cast

from solver import Clue, ClueValue, Clues, EquationSolver, Evaluator, Letter

ACROSS = """
A AW**T – G**I
D W**T – NE**T
I DI**T – L**H
L TN**I – O**I
N HT**T + Y**I
R N**T + O**O + O
S E**E + E**T
Y O**T + W**H
"""

DOWN = """
D DT**I – S
E YE**I + ML**H
G H**M + A**H
H DR**T + OY**H
M WN**H – H**N
O M**H – W
S EI**T – S
T OE**T – R**H
W W**H – GG
"""

GRID = """
XXX.XXX
.X.X...
X...X.X
XX.....
X..X...
"""

# A D E G H I L M N O R S T W Y
# D and S are (1, 10)
# A, I, L, N, R, Y are (4, 7, 9, 13, 14, 15)
# E, G, H, M, O, T, W are (2, 3, 5, 6, 8, 11, 12)
ACROSS_LENGTHS = ((1, 4), (4, 3), (7, 5), (9, 3), (10, 3), (13, 5), (14, 3), (15, 4))
DOWN_LENGTHS = ((1, 3), (12, 2), (2, 5), (3, 3), (8, 3), (10, 3), (5, 5), (6, 2), (11, 3))

DEBUG = True
DRAW_GRID = False

"""
A→ (A * (W ** T)) - (G ** I)
D→ (W ** T) - (N * (E ** T))
I→ (D * (I ** T)) - (L ** H)
L→ (T * (N ** I)) - (O ** I)
N→ (H * (T ** T)) + (Y ** I)
R→ ((N ** T) + (O ** O)) + O
S→ (E ** E) + (E ** T)
Y→ (O ** T) + (W ** H)
D↓ (D * (T ** I)) - S
E↓ (Y * (E ** I)) + (M * (L ** H))
G↓ (H ** M) + (A ** H)
H↓ (D * (R ** T)) + (O * (Y ** H))
M↓ (W * (N ** H)) - (H ** N)
O↓ (M ** H) - W
S↓ (E * (I ** T)) - S
T↓ (O * (E ** T)) - (R ** H)
W↓ (W ** H) - (G * G)
"""


class Magpie256 (EquationSolver):
    steps: int
    parsed_expressions: Sequence[tuple[tuple[Letter, bool], Evaluator]]

    @staticmethod
    def run():
        solver = Magpie256()
        solver.verify_is_180_symmetric()
        solver.alt_solver1()

    def __init__(self) -> None:
        clues, self.clue_names = self.get_clues()
        super().__init__(clues)
        self.expressions = self.parse_expressions()

    def main_solver(self):
        def execute(outer_step):
            function, args = outer_step
            function({}, set(), {}, args)

        def get_value_for_var(known_letters, used_values, board, args):
            letter, allowed_values, next_function, next_args = args
            for value in allowed_values:
                if value not in used_values:
                    used_values.add(value)
                    known_letters[letter] = value
                    next_function(known_letters, used_values, board, next_args)
                    used_values.remove(value)

        def add_to_board(known_letters, used_values, board, args):
            letter, is_across, evaluator, next_function, next_args = args
            clue = self.clue_names[known_letters[letter], is_across]
            result = evaluator.raw_call(known_letters)
            if result > 0 and len(string_result := str(result)) == clue.length:
                locations_set = []
                for location, char in zip(clue.locations, string_result):
                    if (old_char := board.get(location)) is not None:
                        if char != old_char:
                            break
                    else:
                        if char == '0' and self.is_start_location(location):
                            break
                        board[location] = char
                        locations_set.append(location)
                else:
                    # We end up here if we never performed a "break"
                    next_function(known_letters, used_values, board, next_args)
                for location in locations_set:
                    del board[location]

        def print_result(known_letters, _used_values, _board, _args):
            print(known_letters)
            known_clues = {
                clue: ClueValue(value)
                for (letter, is_across), expression in self.expressions
                for clue in [self.clue_names[known_letters[letter], is_across]]
                for value in [str(expression.raw_call(known_letters))]
            }
            self.show_solution(known_clues, known_letters)

        def get_steps():
            steps = []
            known_vars = set()
            for (letter, is_across), evaluator in self.get_sorted_expressions():
                unknown_vars = [var for var in evaluator.vars if var not in known_vars]
                if not (letter in known_vars or letter in unknown_vars):
                    unknown_vars.append(letter)
                known_vars.update(unknown_vars)
                for var in unknown_vars:
                    allowed = (1, 10) if var in "DS" \
                              else (4, 7, 9, 13, 14, 15) if var in "AILNRY" \
                              else (2, 3, 5, 6, 8, 11, 12)
                    steps.append((get_value_for_var, (var, allowed)))
                steps.append((add_to_board, (letter, is_across, evaluator)))
            steps.append((print_result, ()))

            outer_function, outer_args = (lambda *x: None), None
            for (func, args) in reversed(steps):
                outer_args = (*args, outer_function, outer_args)
                outer_function = func
            return outer_function, outer_args

        steps = get_steps()

        start = time.perf_counter_ns()
        execute(steps)
        end = time.perf_counter_ns()
        print(f'{(end - start) / 1_000}us')

    def get_clues(self) -> tuple[Sequence[Clue], dict[tuple[int, bool], Clue]]:
        clues = []
        clue_from_location = {}
        locations = Clues.get_locations_from_grid(GRID)
        for clue_list in (ACROSS_LENGTHS, DOWN_LENGTHS):
            is_across = clue_list == ACROSS_LENGTHS
            for number, length in clue_list:
                clue = Clue(f'{number}{'a' if is_across else 'd'}', is_across,
                            locations[number - 1], length)
                clues.append(clue)
                clue_from_location[number, is_across] = clue
        return clues, clue_from_location

    def parse_expressions(self) -> Sequence[tuple[tuple[Letter, bool], Evaluator]]:
        return [((Letter(key), is_across),  evaluator)
                for expressions in (ACROSS, DOWN)
                for is_across in [expressions is ACROSS]
                for line in expressions.strip().splitlines()
                for key in [line[0]]
                for evaluator in [Evaluator.create_evaluator(line[1:])]]

    def get_sorted_expressions(self) -> Sequence[tuple[tuple[Letter, bool], Evaluator]]:
        result = []
        expressions = {key: value for key, value in self.expressions}
        seen = set()

        def cost(item):
            (key, _is_across), evaluator = item
            variables = (set(evaluator.vars) | {key}) - seen
            total = sum(2 if var in "DS" else 6 if var in "AILNRY" else 6
                        for var in variables)
            return total

        while expressions:
            # We can't just sort because each time we update "seen" which changes the
            # cost function
            key_pair, evaluator = min(expressions.items(), key=cost)
            del expressions[key_pair]
            result.append((key_pair, evaluator))
            seen.update(evaluator.vars)
            seen.add(key_pair[0])
        return result

    def draw_grid(self, location_to_entry, known_letters,
                  location_to_clue_numbers, left_bars, top_bars,
                  **args: Any) -> None:
        if not DRAW_GRID:
            return
        letter_map = {str(value): letter for letter, value in known_letters.items()}
        location_to_entry = {location: letter_map.get(value, value)
                             for location, value in location_to_entry.items()}
        zeros = sorted(location for location, entry in location_to_entry.items()
                       if entry == '0')
        location_to_entry |= dict(zip(zeros, "WDGYLR"))   # WDGYRL
        super().draw_grid(location_to_entry=location_to_entry,
                          **args)

    def alt_solver1(self):
        start = time.perf_counter_ns()
        sorted_clues = self.get_sorted_expressions()

        across_lengths = dict(ACROSS_LENGTHS)
        down_lengths = dict(DOWN_LENGTHS)
        dict1 = [dict(D=D, S=S) for D, S in itertools.permutations((1, 10))]
        dict2 = [dict(A=A, I=I, L=L, N=N, R=R, Y=Y)
                 for (A, I, L, N, R, Y) in itertools.permutations((4, 7, 9, 13, 14, 15))]
        dict3 = [dict(E=E, G=G, H=H, M=M, O=O, T=T, W=W)
                 for (E, G, H, M, O, T, W) in itertools.permutations((2, 3, 5, 6, 8, 11, 12))]

        variables = {}
        for a in dict1:
            variables |= a
            for b in dict2:
                variables |= b
                for c in dict3:
                    variables |= c
                    for (letter, is_across), expression in sorted_clues:
                        value = cast(int, expression.raw_call(variables))
                        if value <= 0 or len(str(value)) != (across_lengths if is_across else down_lengths)[variables[letter]]:
                            break
                    else:
                        print(variables)

        end = time.perf_counter_ns()
        print(f'{(end - start) / 1_000_000_000}sec')

    def alt_solver2(self):
        start = time.perf_counter_ns()
        across_lengths = dict(ACROSS_LENGTHS)
        down_lengths = dict(DOWN_LENGTHS)
        all_variables = [dict(A=A, D=D, E=E, G=G, H=H, I=I, L=L, M=M, N=N, O=O, R=R, S=S, T=T, W=W, Y=Y)
                         for (D, S) in itertools.permutations((1, 10))
                         for (A, I, L, N, R, Y) in itertools.permutations((4, 7, 9, 13, 14, 15))
                         for (E, G, H, M, O, T, W) in itertools.permutations((2, 3, 5, 6, 8, 11, 12))]
        for (letter, is_across), expression in self.get_sorted_expressions():
            print(f'Looking at {letter} := {expression} with {len(all_variables)}')
            lengths = across_lengths if is_across else down_lengths
            all_variables = [variables for variables in all_variables
                             for result in [cast(int, expression.raw_call(variables))]
                             if result >= 10 and len(str(result)) == lengths[variables[letter]]]
        for local in all_variables:
            print(local)
        end = time.perf_counter_ns()
        print(f'{(end - start) / 1_000_000_000}sec')



if __name__ == '__main__':
    Magpie256().alt_solver1()
