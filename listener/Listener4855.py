from collections import defaultdict
from collections import defaultdict
from typing import Iterable, Sequence

from solver import Clues, EquationSolver, Letter
from solver.equation_solver import KnownClueDict, KnownLetterDict

ACROSS = """
1 (BR + A)(N − DN + EW) 
4 I(NF − A + NT) 
6 BE + GIN 
8 M + AITAI 
9 COOT 
11 BA + NG 
12 SLEEP + IN + G + RO + UG − H 
14 (DIR + T)(C − H)E(A + P) 
15 BA(RR + E − D) 
16 F(ER + M − E + NT) 
17 DI(VE + S) 
19 (W + H + I + P)CORD 
21 (RESPO + NS + I + B − L)E 
22 WO + N 
23 PANT 
24 BRA − T 
26 FUN 
27 SPI − T 
28 (U + (ND + A)(U − N)(T − E))D 
"""

DOWN = """
1 HE − AT
2 P(I + N)(PO + I + N) + T + I − N + G
3 (PR + O)(GRE + SS)
4 B + E − T
5 BEAR + H − U − G
6 COCO + NUT
7 (I + N + ST)EAD
9 DRIVER + LESS − VEHI + C − LE
10 (DECA + T)(HLO − N)S
13 I + (N + T + E)NTS
15 IN(CONC + E − RT)
17 C(O − H)EREN + CI + E − S
18 S(E + A)((R + C + H)(L + I + G − H) + T)
20 (FE − N)(D + I + N + G)
22 APA − R − T 
23 BE + A + R + D 
25 HOTRO + D 
"""

ACROSS_LENGTHS = "432/212121/54/333/45/121212/234"
DOWN_LENGTHS="214/412/43/151/232/151/34/214/412"


class Listener4855(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        # solver.plot_board()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self):
        clue_list = self.get_clues()
        super().__init__(clue_list, items=range(10))

    def get_clues(self):
        clue_list = Clues.create_from_text2(ACROSS, DOWN, ACROSS_LENGTHS, DOWN_LENGTHS)
        return clue_list

    def show_solution(self, known_clues: KnownClueDict,
                      known_letters: KnownLetterDict) -> None:
        super().show_solution(known_clues, known_letters)

    def get_letter_values(self, known_letters: dict[Letter, int],
                          letters: Sequence[str]) -> Iterable[Sequence[int]]:
        self.duplicates = self.get_letter_values_with_duplicates(known_letters,
                                                                 len(letters), 2)
        return self.duplicates

    def draw_grid(self, *, known_letters=None, location_to_entry, **args):
        if not known_letters:
            super().draw_grid(location_to_entry=location_to_entry, **args)
            return
        digit_to_letters = defaultdict(str)
        for letter, value in known_letters.items():
            digit_to_letters[str(value)] += letter
        for ((row, column), value) in location_to_entry.items():
            if column in (1, 5, 9):
                location_to_entry[row, column] = "TWODIGITPERFECTNUMBER"[(column - 1) // 4 * 7 + (row - 1)]
        shaded_squares = [location for location, value in location_to_entry.items() if value in ('2', '8')]
        super().draw_grid(known_letters=known_letters,
                          shading=dict.fromkeys(shaded_squares, 'red'),
                          location_to_entry=location_to_entry, font_multiplier=0.8, **args)


    # self.draw_grid(max_row=max_row, max_column=max_column,
    #                clued_locations=clued_locations,
    #                clue_values=clue_values,
    #                location_to_entry=location_to_entry,
    #                location_to_clue_numbers=location_to_clue_numbers,
    #                top_bars=top_bars,
    #                left_bars=left_bars, **more_args)


if __name__ == '__main__':
    Listener4855.run()


