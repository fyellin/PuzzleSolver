import itertools
import re
import string
from collections import Counter, defaultdict
from typing import Unpack

from solver import Clue, Clues, ConstraintSolver, DrawGridArgs, Location, generators, \
    KnownClueDict

ACROSS = """
9 Present song losing essential character in transmission down line (8;2,5) HERE,DITY
12 Gutless mob leaving fighting in Ulster? (4;1,3) COAT
14 Rubbish service disappeared abruptly (6;5,3) RAF,FLE
15 World energy growth is overwhelming (6;2,6) PLAN(E)T
16 Having left hospital, doctor concealed stiff (5;2,4) RIG,ID
17 What is due to leave inhospitable place? (6;1,5) DESERT
18 Lament country moving over to the right (4;3,1)  MOAN
20 Blunder by Congress seized upon by right-wing state? (9;1,7) T(ERR,IT)ORY
22 I’m doubtful about choice of words welcoming adult’s removal (11;5,8) ER,A,DIC(A)TION
25 Policy favouring Union is initially met by disorder following Conservative’s dismissal (9;2,6) FUSION,IS,M
28 May I ask how victim is reported? (4;3,1) PRAY
29 Association helping to make available a guest-house (6;2,5) LEAGUE
31 Actor’s last to enter cast in tiny part (5;1,2) SH(R)ED
33 Buy everything available to control embarrassing situation (6;2,1) CORNER
34 Moody, silent star conveys lines with ease in the end (6;6,3) SU(LL,E)N
35 Informal agreement is better over time (4;1,3) PAC<,T
36 Name individual who’s derisive about part of UK (8;1,8) MO(NI)CKER
"""

DOWN = """
1 A great many like wearing one in Pride (6;6,4) L(EG)ION
2 Grey edges in imbedded diagram shown above (4;1,4)  GR,ID
3 Unite strike upended railway (5;3,1) MAR,RY
4 Show accepted source of illustration in French (4;2,3) F(A,I)R
5 Filling in odd crack in tunnel (5;3,2) [o]D[d],RIFT
6 General finally put a stop to advance (4;3,2) L,END
7 Set visible to the audience (6;1,4) INCITE
8 Dog bites bottom of another dog (5;5,4)  T(R)AIL
10 Countries support end of emissions (6;2,1) SHORE,S 
11 Article picked up on misrepresentation of true cosmos (6;4,1) NA,TURE
13 A disciple? (6;5,3)PER,SON 
19 Cope with skin inflammation round top of arm (6;3,2) MAN(A)GE
20 Put research into, say, drawing's caption (6;6,1) AR(RES)T
21 Pitch provides support for this? (6;6,4) HOCKEY
23 Withdraw outdated green short trench coats (6;2,4) RECOIL
24 Variegated trees clumped together in California meadow (6;3,1) MOT,LEY
26 A German newspaper grapples with rules (5;1,3) 
27 Suffer ruin recklessly importing cocaine (5;1,5) IN(C)UR*
28 What’s behind short plant? (5;1,3) ASTER
30 Briefly reach a state of unconsciousness (4;4,2) COM,A
31 Entrance to passageway is missing key (4;2,4) ISLE
32 Uncovered bit of gold overlooked in dig (4;3,4) NUDE
"""

GRID = """
.XXXX.XX.X.X.
X....X..XXX..
.X.....X.....
X.....X......
X.X.X..X.....
.X.X.......X.
XX....X..X...
.X...X..X.X..
X.....X......
X....X.......
.............
"""

class Magpie263b(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False)
        solver.plot_board()

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues)
        self.fixed = {}
        self.solutions = []
        for clue in clues:
            word, start, end = clue.context
            if not word:
                continue
            self.fixed[clue.location(0)] = word[start - 1]
            self.fixed[clue.location(clue.length - 1)] = word[end - 1]

    def get_clues(self):
        grid = Clues.get_locations_from_grid(GRID)
        clues = []
        for lines in (ACROSS, DOWN):
            is_across = lines is ACROSS
            for line in lines.strip().splitlines():
                line = line.strip()
                match = re.fullmatch(r'(\d+)\s*.*\((\d+);(\d+),(\d+)\)(.*)', line)
                number, length, start, end, word = match.groups()
                number, length, start, end = map(int, (number, length, start, end))
                word = ''.join(x for x in word if x in string.ascii_uppercase)
                name = str(number) + ("a" if is_across else "d")
                clue = Clue(name, is_across, grid[number - 1], length)
                clue.context = (word, start, end)
                if word:
                    clue.generator = self.get_generator(clue)
                clues.append(clue)
        return clues

    def show_solution(self, known_clues: KnownClueDict) -> None:
        self.solutions.append(known_clues.copy())

    def get_generator(self, clue):
        word, start, end = clue.context
        counter = Counter(word)
        letter1, letter2 = word[start - 1], word[end - 1]
        counter[letter1] -= 1
        counter[letter2] -= 1
        permutations = set(itertools.permutations(counter.elements()))
        permutations = [letter1 + ''.join(p) + letter2 for p in permutations]
        return generators.known(*permutations)

    def get_allowed_regexp(self, location: Location) -> str:
        return self.fixed.get(location, '.')

    def draw_grid(self, location_to_entry, **args: Unpack[DrawGridArgs]) -> None:
        location_to_entries = defaultdict(set)
        for solution in self.solutions:
            for clue, value in solution.items():
                for location, letter in zip(clue.locations, value):
                    location_to_entries[location].add(letter)

        location_to_entry = {}

        for location, entries in location_to_entries.items():
            if len(entries) == 1:
                location_to_entry[location] = entries.pop()
            else:
                location_to_entry[location] = ''.join(sorted(entries)).lower()
        super().draw_grid(location_to_entry=location_to_entry,
                          font_multiplier=.5,
                          **args)


if __name__ == '__main__':
    Magpie263b.run()
