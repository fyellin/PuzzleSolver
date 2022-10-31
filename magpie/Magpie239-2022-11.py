import itertools
import math
from collections.abc import Iterable
from typing import Any

from solver import Clue, ClueValue, Clues, EquationSolver, Evaluator, Letter
from solver.equation_parser import EquationParser
import fractions

from solver.equation_solver import KnownClueDict, KnownLetterDict

GRID = """
X.XXX.XX
.X.X.X..
X..XX.X.
X.X..X..
X...X..X
XX.X..X.
.XX.XX.X
X...X...
X....XX.
.X...X..
"""

ACROSS = """
1 AD + R – D (3)
3 D + URU (4)
8 DR+OR (2)
9 E + NS – P (3)
10 NIR – I (3)
12 (D + I)G + T (3)
15 AP + R + G (3)
16 STI – DN (3)
17 (HD – N)N (4)
18 (I + N)OY + P (4)
20 IS – P – I (3)
22 GY + EO (4)
24 I + (A/I)(R + D) (4)
27 (S – P)/R – P (2)
29 I(T+S + SEM+AP+HO–R–E) (4)
30 (E – M)O/I – A (4)
31 N+TH + GRI–D – S–T+E–P+S (3)
32 M+IND – T+H+E + (G+A)P (3)
34 (R+(O–M+A–N + O)N)D+IAG (4)
35 GR – D + I (3)
"""

DOWN = """
1 DU(U + TI) (3)
2 DRSI**R (4)
4 G + ES (3)
5 U(G – M) (2)
6 TIRO – M (4)
7 DUER – D (4)
11 D**DYI – I (3)
13 D(U(A – M) – T) (3)
14 HID+DE–N – MO+RSE (4)
16 MNA(I + D) (3)
19 E + G/D (2)
21 IRR**R/I**I – I (3)
22 YOA + RI (4)
23 TH–REE + DIMEN+(S+I)(O–N+S) (3)
25 OI(I + P)D (4)
26 TR(NO – M) (4)
27 (H + IG/(H – S))T – E (3)
28 H**I U + YI (4)
29 UP+PI–N+G+H+A–M (3)
33 (S – T)**D (2)
"""

class Magpie239(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie239()
        # solver.plot_board()
        solver.solve(debug=False)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 23))
        self.squares = {str(i * i) for i in range(100)}
        self.sum_of_squares = {str(x): (i, j) for i in range(100) for j in range(100)
                               for x in [i * i + j * j] if x <= 10000}

        def not_square(x):
            return x not in self.squares

        def not_square2(x, y):
            return not (x in self.sum_of_squares and y in self.sum_of_squares)

        for clue1 in clues:
            self.add_constraint((clue1,), not_square)
        for clue1, clue2 in itertools.permutations(clues, 2):
            self.add_constraint((clue1, clue2), not_square2)

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        locations = [(row, column + 1) for row, column in locations]
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)

        for clue in clue_list:
            if clue.is_across:
                self.redo_evaluator(clue)
        return clue_list

    def redo_evaluator(self, clue: Clue):
        equation_parser = EquationParser()
        parse, = equation_parser.parse(clue.expression)
        variables = sorted(parse.vars())
        parsed_expression = parse.to_string(frozenset())
        squared_expressions = [
            f"{parsed_expression[0:i]}({letter}*{letter}){parsed_expression[i + 1:]}"
            for i, letter in enumerate(parsed_expression)
            if letter in variables]
        codes = [f"lambda {', '.join(variables)}: {e}" for e in squared_expressions]
        compiled_codes = [eval(code, {}, {}) for code in codes]

        def my_wrapper(_evaluator: Evaluator, value_dict: dict[Letter, int]
                       ) -> Iterable[ClueValue]:
            args = [fractions.Fraction(value_dict[x]) for x in variables]
            results = set()
            for code in compiled_codes:
                try:
                    result = code(*args)
                    int_result = int(result)
                    if result == int_result > 0:
                        results.add(ClueValue(str(int_result)))
                except ArithmeticError:
                    pass
            return results

        evaluator = Evaluator(my_wrapper, compiled_codes[0], variables, clue.expression)
        clue.evaluators = evaluator,

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        self.show_letter_values(known_letters)
        self.plot_board(known_clues, known_letters=known_letters)

    def draw_grid(self, **args: Any) -> None:
        args['max_column'] += 1
        args['clued_locations'] |= {(row, column) for row in range(1, 11) for column in (1, 10)}
        args['left_bars'] |= {(i, 10) for i in range(1, 11)}
        args['top_bars'] -=  {(i, 1) for i in range(2, 11)}

        shaded_squares = {(2, 1), (3, 1), (4, 1), (5, 1), (1, 10), (2, 10), (3, 10), (7, 10)}
        args['subtext'] = f'$\\bf{{3^2 + 4^2 = 5^2}}$' #
        args['shading'] = {x : 'lightgray' for x in shaded_squares}

        clue_values = args['clue_values']
        value_to_letter = {value: letter for letter, value in args['known_letters'].items()}
        for row in range(1, 11):
            clues = [clue for clue in self._clue_list
                     if clue.is_across and clue.location(0)[0] == row]
            assert len(clues) == 2
            clues.sort(key=lambda clue: clue.location(0)[0])
            for clue, column in zip(clues, (1, 10)):
                total = sum(int(digit) for digit in clue_values[clue])
                args['location_to_entry'][row, column] = value_to_letter[total]
        super().draw_grid(**args)


"""

        def draw_grid(*, max_row: int, max_column: int,
                      clued_locations: Optional[set[Location]] = None,
                      location_to_entry: dict[Location, str] = None,
                      location_to_clue_numbers: dict[Location, Sequence[str]] = None,
                      top_bars: set[Location] = frozenset(),
                      left_bars: set[Location] = frozenset(),
                      shading: dict[Location, str] = None,
                      rotation: dict[Location, str] = None,
                      circles: set[Location] = frozenset(),
                      subtext: Optional[str] = None,
                      font_multiplier: float = 1.0,
                      blacken_unused: bool = True,
                      file: Optional[str] = None,
                      grid_drawer: Callable[[plt, Axes], None] = None,
                      extra: Callable[[plt, Axes], None] = None,
                      **args: Any) -> None:
"""

if __name__ == '__main__':
    Magpie239.run()
    # solver = Magpie239()
    # clues = {'21d': '510', '10a': '966', '24a': '1136', '1a': '973', '2d': '3264', '17a': '1760', '3a': '1299', '7d': '1617', '28d': '3275', '11d': '700', '22d': '2348', '8a': '76', '25d': '1380', '18a': '1971', '20a': '555', '9a': '391', '27a': '46', '14d': '1158', '30a': '1102', '16d': '990', '29a': '2034', '26d': '6104', '6d': '1119', '16a': '919', '1d': '999', '13d': '417', '23d': '660', '33d': '27', '22a': '2406', '34a': '6054', '15a': '406', '32a': '927', '27d': '419', '35a': '575', '4d': '267', '12a': '734', '31a': '638', '29d': '268', '5d': '99', '19d': '19'}
    # values = {'I': 2, 'R': 4, 'N': 11, 'A': 18, 'D': 3, 'S': 17, 'H': 19, 'U': 9, 'E': 15, 'Y': 13, 'O': 10, 'P': 21, 'M': 1, 'T': 14, 'G': 12}
    # clues = { solver.clue_named(name): value for name, value in clues.items()}
    # solver.plot_board(clues, known_letters=values)
