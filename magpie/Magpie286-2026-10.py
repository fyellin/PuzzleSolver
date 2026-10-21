import re
from collections.abc import Iterable, Sequence
from typing import Unpack

import more_itertools

from solver import (
    Clues,
    DrawGridKwargs,
    EquationSolver,
    KnownLetterDict,
    Location,
)
from solver.helpers import is_square, is_triangular

ACROSS_LENGTHS = "44/242/323/323/242/44"
DOWN_LENGTHS = "33/231/123/321/123/321/132/33"

ACROSS = """
1 TO×RR
4 (B−I+G)×BET
7 QU−IT
8 CR×E×D×I×T
10 B×AR
11 QU×I+NO−A
13 QU−A−S+I
14 UNT−IE
15 SC×R+E−A−M
17 M+E
19 (GE+R)×M
21 R×(O+B)
22 HA×UG×H
23 ALI−VE
24 L×ANAI
25 VI×TA×L
"""

DOWN = """
1 DR×O×O×L
2 R×E×A+D
3 (V+E)×TS
5 (A+I)×OLI
6 EUR−O−S
8 B×O×T+H
9 H×(I+V+E)
10 M×ADE
12 M+AT×IN
15 DIG×(I+T)
16 C×A×BS
17 A×I×R
18 (H+A)×RM+S
19 M×AD
20 GO+RE
23 SA+T
"""


class Magpie286(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        # solver.plot_board()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 10))

    def get_clues(self):
        return Clues.create_from_text2(ACROSS, DOWN, ACROSS_LENGTHS, DOWN_LENGTHS,
                                       rewrite_expression=self.rewrite_string)

    def get_allowed_regexp(self, location: Location) -> str:
        return '[^0]'

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[
            Sequence[int]]:
        return self.get_letter_values_with_duplicates(known_letters, len(letters), 2)

    def rewrite_string(self, expression: str) -> str:
        def convert_concat_to_decimal(match: re.Match[str]) -> str:
            letters = match.group()
            terms = (f'{10 ** power} * {letter}' if power else letter
                     for power, letter in zip(range(len(letters)), letters[::-1], strict=True))
            return f'({" + ".join(terms)})'
        return re.sub(r'[A-Z]{2,}', convert_concat_to_decimal, expression)

    def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
        grid = args['location_to_entry'].copy()
        known_letters = args['known_letters']
        int_to_letters = more_itertools.map_reduce(known_letters, keyfunc=known_letters.__getitem__)
        int_to_entry = {key: ''.join(sorted(value)) for key, value in int_to_letters.items()}
        grid2 = {location: int_to_entry[int(value)] for location, value in grid.items()}
        args['location_to_entry'] = grid2
        super().draw_grid(**args)

        args['location_to_entry'] = grid
        for row in range(1, 7):
            for column in range(1, 3):
                squares = ((row, column + i) for i in range(7))
                value = int(''.join(grid[square] for square in squares))
                if is_triangular(value) and is_square(value):
                    squares = ((row, column + i) for i in range(7))
                    args['shading'] = dict.fromkeys(squares, 'red')
        super().draw_grid(**args)


if __name__ == '__main__':
    Magpie286.run()
