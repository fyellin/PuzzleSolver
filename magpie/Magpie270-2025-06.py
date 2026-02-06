from typing import Any

from solver import Clues, EquationSolver, Location

ACROSS_LENGTHS = "324/243/13131/342/423"
DOWN_LENGTHS = "41/32/32/23/212/32/23/23/14"

ACROSS = """
1 (D + O)(D + O)
4 C + OT + T + ONON
*6 (R – E + A – S)S – UMES
*9 COM – A
10 COMPE + TITI + (V – E – NE – S)S
*11 SH(AV – E) – R
*13 R – EPAST
15 TIMP(A + N) – I – S – T
18 OUTRO + O – T
*21 ((E + A – R – T – H + T + R)E – M)OR
*24 AWAIT
25 (RE – T)R(A – NS – M + I)T
26 D + O
*27 SL + E – UTHS"""

DOWN = """
*1 R(E + I + NED)
2 DOWS – I + N + G + R – O + D
*3 NE + A + R – M – ISS
4 (S – O)ON
*5 SO – I + L
*6 (M + I)(D – G)(E – T)
*7 W + ALLOON
8 MOAN
12 SHIR + TTA + I(L – S)
*14 HEPT + A + GO + N
16 CAMP(A – I + G) + N
17 A – MP(L + IT – U + D – E)
*19 DU + LL
*20 G – O + ADS
*22 S – O
*23 CU + T
"""

class Magpie270 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        across, down = self.munge(ACROSS), self.munge(DOWN)
        clues = Clues.create_from_text2(across, down, ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues, items=(x for x in range(-9, 10) if x != 0))

    def munge(self, text: str) -> str:
        new_lines = []
        for line in text.split('\n'):
            if line.startswith('*'):
                number, info = line.split(' ', 1)
                line = f'{number[1:]} -({info})'
            new_lines.append(line)
        result = '\n'.join(new_lines) + '\n'
        return result

    def draw_grid(self, **args: Any) -> None:
        # super().draw_grid(**args, font_multiplier=.8)
        info = [[] for _ in range(10)]
        known_letters = args['known_letters']
        for letter, value in known_letters.items():
            info[abs(value)].append(letter)
        info = [''.join(sorted(x)) for x in info]
        location_to_entry = args['location_to_entry']
        # super().draw_grid(**args)
        for location, entry in location_to_entry.items():
            location_to_entry[location] = info[int(entry)]
        # super().draw_grid(**args, font_multiplier=.6)
        quotation = "ACCENTTCHUATETHEPOSITIVEELIMINATE           "
        shading = {}
        for index, location in enumerate(sorted(location_to_entry.keys())):
            location_to_entry[location] = quotation[index]
            if 13 <= index <= 23:
                shading[location] = 'red'
        super().draw_grid(**args, shading=shading, font_multiplier=.8)

    def get_allowed_regexp(self, location: Location) -> str:
        return '[1-9]'


if __name__ == '__main__':
    Magpie270.run()
