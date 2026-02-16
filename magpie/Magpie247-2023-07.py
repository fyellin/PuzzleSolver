from solver import Clues, EquationSolver, KnownClueDict, KnownLetterDict

GRID = """
XXXXXXXX
.X.X.X..
XXX..X..
X.X.XX.X
XX..X.X.
X..X.XXX
X.X.X.X.
X.X..X..
"""

ACROSS = """
1 GE + O + M + E + T + R + Y (3)
4 ADD – O + N + E            (3)
7 D + E– C + O + D – E       (2)
9 S + A! + M! + O + A!       (3)
11 C**H + EA + T             (3)
12 COSY                      (2)
14 DR + A!C + O              (3)
15 COMM – O + N + (D + E)N – O – M + IN + A + TOR (3)
16 DADA – I – S + T – I/C    (4)
19 C**HOC                    (3)
21 (C + H)EE – R + S – N – U + D + D (3)
23 C + R + U + N + (CH)**Y   (4)
25 T + R + E + A + S+ U + R + E + H + U + N +T + S (3)
26 SC**A + R                 (3)
28 COD                       (2)
30 ((T + H + I)R + T)/Y      (3)
32 SO(RR + Y)                (3)
34 MA/C                      (2)
35 A**S + COT                (3)
36 SA + S!H                  (3)
"""

DOWN = """
1 NO + UG – H + T (3) 
2 G + R – E + A +T – E – R + T + H + A + N (2)
3 H + I + DD + E + N + H + AR + E + S (3) 
5 T(RA – Y) (3)
6 D + E + D + U + C +T (2)
7 S**A + N**C + H – O – S (4)
8 STA+Y**S               (3)
10 RE + D!               (4)
13 A + CR + O + SS       (2)
15 IC**Y + ROAD + A + HE + A + D (3)
16 O +D +E               (2)
17 I – N + TE – RS + E + CT + I + O – N (3)
18 H + A – T – E + M – Y + SUMS (4)
20 T – H + I – R +T + Y  (2)
22 (H + A)M! + O – R – E – GG + S (4)
24 M + A**C              (2)
25 I – N + TE + G – E – R (3)
26 COSI + N – E           (3)
27 C(O + S + E + C) + ANT (3)
29 (R + A + T + I – O)N (3)
31 COCOS (2)
33 H + E + I + G – H –T (2)
"""
class Listener4764(EquationSolver):
    @staticmethod
    def run():
        solver = Listener4764()
        # solver.plot_board({})
        # solver.verify_is_180_symmetric()
        solver.solve(debug=0)

    def __init__(self):
        clues = self.get_clues()
        # print(clues[9])
        # del clues[9]
        print(len(clues))
        super().__init__(clues, items=range(1, 16))

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        return clue_list

    def draw_grid(self, **args) -> None:
        super().draw_grid(subtext="YOU JUST GET USED TO THEM", **args)

if __name__ == '__main__':
    Listener4764.run()

"""
14 12 65 13 8965 13 14 2431 15 7112131512791041351271381412114 12915651212
I  N  MA T  HEMA T  I  CSYO U  DON T U N DER ST AN DT HI N G S  N  EU MAN N
O  C  Y  S  A  M  D  H  E  R  G  N  T  I  U 
1  2  3  4  5  6  7  8  9  10 11 12 13 14 15
"""
