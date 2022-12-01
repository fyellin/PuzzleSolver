import itertools
from collections.abc import Iterable
from typing import Any, Sequence

from solver import ClueValue, Clues, EquationSolver, Evaluator, Letter, Location
from solver.equation_solver import KnownLetterDict

GRID = """
X.XXXXXXXX
X....X....
XXX...X.XX
X..X..X...
.X..XX.X..
X.X.XX.XX.
XX...XX.XX
X.....XX..
X...X.X...
"""

ACROSS = """
1 −M + AS + S! (4)
4 S + T + R − A − N − G + E (2)
6 SPIN − O + R (4)
10 −P + AR + T + ICL + E (4)
11 ((P + H)(O − N)/O**N)! = 40320 (5)
12 A + T + O! + M − I + C (2)
14 G(A + U + G + E) (3)
16 IO − NS (2)
18 H − I + GG + S (3)
19 B(A − R + N) (3)
20 (P + L)(AS + M − O! − N) (4)
21 −P − OT − E**N + T + IAL (4)
23 N + E + U − TR + (O − N)S! (4)
25 T(O! + P) (4)
27 B(O + S + O + N) (3)
29 TU + N − N + E + L (3)
31 B − O − S + E (2)
33 (P − I − ON)! (3)
35 C + H − A − R + M (2)
37 B + OTTO + M (5)
38 NI + ELS (4)
40 S!/O − (L − I + TO)N (4)
41 B − O + R**N (2)
42 N + UCL − E + AR (4)
"""

DOWN = """
1 M + (E + A + S − U)(R + E) (3)
2 T + A − U (2)
3 (−S + I)(N − G + L + E + T) (3)
4 (N − E + U + T + R)(I − N)O (4)
5 M + UM − E + S!(O! − N) + S (5)
7 C + O − L + LAP + S − E (4)
8 (S!/P − I)**N (3)
9 −P + SI − O − N − S (2)
13 −S + L − I + T (2)
14 UP (3)
15 (−E + (I + N!)S + T − E)IN (4)
17 M + O − L + ECU − L + E (4)
18 (T + E + NSO)R (4)
19 (C + H + RO)NO − N! − S (4)
22 I + S + O**S − P + I**N (5)
24 (C/O)LOU/R (3)
26 P + OS! + I + T + I − O − N! (4)
28 PO(S + I − T + R + O + N) (4)
30 −G − L + UO + N! (2)
32 P + HA + S + E − S (3)
34 −B − O + HR (3)
36 EL + E − C + T + R − O + N (3)
37 −M + UO/N (2)
39 −S + T + R + I + N − G (2)
"""


class Listener4738(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Listener4738()
        solver.solve(debug=True, max_debug_depth=2, multiprocessing=True)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=range(2, 34, 2))

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        for clue in clue_list:
            if not clue.is_across:
                clue.evaluators[0].set_wrapper(self.down_wrapper)
            if clue.name == '33a' and False:
                evaluator = Evaluator.create_evaluator("0", wrapper=self.fixed_wrapper)
                clue.evaluators = (*clue.evaluators, evaluator)
        return clue_list

    def get_allowed_regexp(self, location: Location) -> str:
        match location:
            case (7, 6): return '[17]'
            case (7, 7): return '2'
            case (7, 8): return '0'
        return super().get_allowed_regexp(location)

    @staticmethod
    def down_wrapper(evaluator: Evaluator, value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
        try:
            result = evaluator.compiled_code(*(value_dict[x] ^ 1 for x in evaluator.vars))
            int_result = int(result)
            if result == int_result > 0:
                return ClueValue(str(int_result)),
            return ()
        except ArithmeticError:
            return ()

    @staticmethod
    def fixed_wrapper(_evaluator: Evaluator, _value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
        yield from [ClueValue(str(120)), ClueValue(str(720))]

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[Sequence[int]]:
        count = len(letters)
        if count == 0:
            yield ()
            return
        unused_values = [i for i in self._items if (i & ~1) not in set(known_letters.values())]
        for values in itertools.permutations(unused_values, count):
            for xors in itertools.product((0, 1), repeat=count):
                yield [value ^ xor for value, xor in zip(values, xors)]

    def draw_grid(self, max_row, clue_values, left_bars, top_bars, location_to_entry,
                  clued_locations, **args: Any) -> None:
        max_row += 3
        clued_locations |= {(row, column) for row in range(10, 13) for column in range(1, 11)}

        top_bars |= {(10, i) for i in range(1, 11)}

        for row in range(0, 3):
            for column in range(1, 11):
                values = [location_to_entry[row * 3 + i, column] for i in range(1, 4)]
                total = sum(int(value) for value in values)
                if 1 <= total <= 26:
                    location_to_entry[10 + row, column] = chr(total + 64)
                else:
                    location_to_entry[10 + row, column] = str(total)
        color1 = 160/256, 189/256, 223/256, .5
        color2 = 206/256, 218/256, 102/256, .5
        color3 = 251/256, 187/256, 194/256, .5
        shading = {}
        shading |= {(row, column): color1 for row in (1, 2, 3, 10) for column in range(1, 11)}
        shading |= {(row, column): color2 for row in (4, 5, 6, 11) for column in range(1, 11)}
        shading |= {(row, column): color3 for row in (7, 8, 9, 12) for column in range(1, 11)}

        super().draw_grid(clue_values=clue_values, left_bars=left_bars, top_bars=top_bars,
                          location_to_entry=location_to_entry,
                          clued_locations=clued_locations,
                          max_row=max_row,
                          font_multiplier=.8,
                          shading=shading,
                          # extra=self.extra,
                          **args)

    @staticmethod
    def handle_finish_up():
        solver = Listener4738()
        known_letters = dict(zip("ABCEGHILMNOPRSTU",
                                 (15, 13, 17, 23, 10, 33, 18, 21, 28, 2, 4, 31, 9, 7,  26, 25)))
        known_values = {clue: str(clue.evaluators[0](known_letters)[0])
                        for clue in solver._clue_list}
        solver.plot_board(known_values)
        # solver.show_letter_values(known_letters)

if __name__ == '__main__':
    Listener4738.run()
    #  Listener4738.handle_finish_up()
