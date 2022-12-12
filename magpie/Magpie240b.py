import re
from collections import Counter, defaultdict
from typing import Any

from solver import Clue, Clues, EquationSolver

GRID = """
..X.XXX.X..X..
..X......X...X
..X.X..XX..X..
...XX.X.......
.XX...........
..X.XX.....X.X
..X...X.X.XXX.
........X.....
.X.......XX.XX
..X........X..
.....X......X.
"""

ANSWERS = \
"""
1 -------------
8a Large member of Daphne’s family is a reptilian monster (5) AGILA
9d Atmospheric lights are coming back, George said (7) AIRGLOW
2 -------------
2d Unusual to stream comprehensive school subject (6) COMPART
3d Checks on part of ship’s support (6) STEMSON
19a Old, spiritless, rejecting support network having ditched society (5) AMORT
28a Pessimistic philosophy graduate with Iris Murdoch’s preface (6) MALISM
39a Stranraer’s close, but Northern Ireland’s closer to Galway (5) NIRLY
3 ---------------
3a Organ drained of some energy by two large muscles (6) SPLENII
4a Comedy routine has naughty child ultimately expelled after school (6) SCHTIK
7a Ian’s getting involved in case to confess, admitting it’s wrong (6) SISTING
16a Going out with goddess, Jack’s transfixed (5) HEJRA
31a He uncaps such a pen that’s explosive, having twice the necessary guts? (7) PAUNCHES
4 --------------
10a Noblewoman to ruin tea,, drinking last drops of apple schnapps (7) MARCHESA
14a Former teachers tutor elsewhere – each exhausted Hazel? (7) NUTTREE
15a Inhabitant’s extremely uncharitable leaving rest of estate to former Queen (6) RESIDER
24a Spring lines in body of water on the ebb (6) LOLLOP
27d Known venture capitalist’s in trouble, denying botched space travel (6) INTUIT
5 --------------------
12d I eat about 100 nuts with vinegar (5) ACETIC
18a Sabbatean Crypto-Jews put on edge from the East (6) DONMEH
34d Formed lacuna for this? (5) CANULA
36a Insanity of shrinks on couch (4) FOLIE
6 ---------------------
11d Prince losing head over shooting equipment? (5) ORTHO
20d Tackle has club substituting Hearts old striker (6) MCCOIST
30a Horribly spat at European referee’s back, having lost 4 down (8) ASEPTATE
7 ----------------------------
32a See breaking points (6) STOPIN
38d Charger’s covering is taut and not rolled (8) CHAFFRON
40d Drunk damson spirits (5) MONADS
8 ----------------
17d Essentially, stress buster occurs hereby? (7) RESTCURE
9 ------------------
12d Regularly manumit nursing pages and maid (5) APPUI
22d Brig cracks are relevant to an old ship (6) ARKITE
10 --------------------------
1d Moore is obsessing over clothes basket material (4) OSIER
4d Gags taking snipe ultimately brought about division (6) SEPTUM
23d Hate nationalist following card (4) CURN
11 --------------------
21d Unclued (6) SAFETY
26a Name good for Sikh’s king? (4) SINGH
37a Track expanded by including a section from recording (4) PISTE
12 --------------------
29a More attractive boozer (6) LUSHER
33d Sent back swatch to cover over torn linen dress materials (9) EOLIENNES
13 ----------------------
6d Is ghoul flying out of Hungary a one for him? (6) LUGOSI
14 -------------------
15a Respond to getting Satan finally exorcised by church, like so? (7) REJOICE
25a Carpenter drops 2nd and 7th pillars (5) CIPPI
15 ---------------------
5a Mate wants back payment for value of shares? (3) PAR
17 -------------
38a Flying toucans’ natural impulse (7)  CONATUS
18 ------------------
23a Ed’s cold purée is delivered (5) COOLY
20 --------------
13a Smells endlessly satisfying, locally (3) NUFF
26a Inserts in a puzzle special prizes (5) SLOTS
35a Introduction of school by Scottish peers (6) STIMES
"""

"""    
    
2d ['C', 'O', 'M', 'PA', 'R', 'T'] COM[A]RT: A
3d ['S', 'T', 'E', 'MS', 'O', 'N'] STE[P]ON: P
3a ['S', 'P', 'L', 'E', 'N', 'II'] SPLEN[T]: T
7a ['S', 'IS', 'T', 'I', 'N', 'G'] S[AI]TING: I
31a ['PA', 'U', 'N', 'C', 'H', 'E', 'S'] [BDHLMPR]UNCHES: R
10a ['M', 'A', 'R', 'C', 'H', 'E', 'SA']   MARCHE[NRS]: R
15a ['R', 'E', 'SI', 'D', 'E', 'R'] RE[ADEN]DER: N
12d ['A', 'CE', 'T', 'I', 'C'] A[NRT]TIC: T
34d ['CA', 'N', 'U', 'L', 'A'] [I]NULA: I
36a ['F', 'O', 'L', 'IE'] FOL[DK]: D
20d ['M', 'CC', 'O', 'I', 'S', 'T'] M[A]OIST: A 
40d ['M', 'O', 'N', 'A', 'DS'] MONA[DLS]: S
17d ['R', 'E', 'S', 'T', 'CU', 'R', 'E'] REST[O]RE: O
1d ['OS', 'I', 'E', 'R'] [BFKLPTV]IER: T
26a ['S', 'I', 'N', 'GH'] SIN[DEGHKS]: E
37a ['P', 'IS', 'T', 'E'] P[AO]TE: A
13a ['NU', 'F', 'F'] [AEIO]FF: O
"""


class Junk(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Junk()
        solver.go()

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=())

    def go(self):
        extra_clues = []
        locations = {}
        for clue in self._clue_list:
            if word := clue.context:
                if len(word) == clue.length:
                    for (letter, location) in zip(word, clue.locations):
                        locations[location] = letter
                else:
                    extra_clues.append(clue)

        work_done = True
        while work_done:
            work_done = False
            old_length = len(extra_clues)
            extra_clues = [clue for clue in extra_clues
                           if not self.extra_clue_resolve(clue, locations)]
            if len(extra_clues) != old_length:
                work_done = True
            print(old_length, len(extra_clues))

            alt_locations = defaultdict(list)
            for clue in extra_clues:
                word = clue.context
                for i, location in enumerate(clue.locations):
                    if location not in locations:
                        alt_locations[location].append({word[i], word[i+1]})
            for location, entries in alt_locations.items():
                if len(entries) >= 2:
                    letters = set.intersection(*entries)
                    if len(letters) == 1:
                        locations[location] = letters.pop()
                        work_done = True

        result = {clue: [locations[location] for location in clue.locations]
                  for clue in self._clue_list if clue.context}
        for clue in self._clue_list:
            assert ''.join(result[clue]) == clue.context

        self.plot_board(result)

    def extra_clue_resolve(self, clue, locations):
        word = clue.context
        known = [locations.get(location) for location in clue.locations]
        busted = list(word)
        possibilities = []
        for i in range(len(word) - 1):
            possibility = busted[:]
            possibility[i:i+2] = [possibility[i] + possibility[i + 1]]
            assert len(possibility) == clue.length
            if all(known[i] is None or known[i] == possibility[i]
                   for i in range(clue.length)):
                possibilities.append(possibility)
        if len(possibilities) == 1:
            possibility, = possibilities
            for location, letter in zip(clue.locations, possibility):
                locations[location] = letter
            return True
        else:
            return False

    def get_clues(self):
        skip = None
        clues = []
        seen_names = set()
        locations = Clues.get_locations_from_grid(GRID)
        for answer in ANSWERS.splitlines():
            answer = answer.strip()
            if not answer:
                continue
            if match := re.match(r'^(\d+) ----', answer):
                skip = int(match.group(1))
            else:
                match = re.fullmatch(r'((\d+)\w?[ad]) .+ \((\d+)\)(\s+(\w+))?', answer)
                clue_name, clue_number, length, _, word = match.groups()
                if clue_name in seen_names:
                    clue_name = clue_name[:-1] + 'x' + clue_name[-1]
                seen_names.add(clue_name)
                clue_number, length = int(clue_number), int(length)
                location = locations[clue_number - 1]
                is_across = clue_name.endswith('a')
                clue_locations = self.get_clue_locations(location, skip, length, is_across)
                clue = Clue(clue_name, is_across, location, length,
                            locations=clue_locations, context=match.group(5))
                clues.append(clue)
        return clues

    def get_clue_locations(self, location, skip, length, is_across):
        row, column = location
        result = [location]
        for _ in range(length - 1):
            if is_across:
                column += skip
                while column >= 15:
                    row, column = row + 1, column - 14
                    if row >= 12:
                        row = row - 11
            else:
                row += skip
                while row >= 12:
                    row, column = row - 11, column + 1
                    if column >= 15:
                        column = column - 14
            result.append((row, column))
        return result

    def draw_grid(self, location_to_entry, top_bars, left_bars,
                  **args: Any) -> None:
        # Verify we've entered values correctly
        for clue in self._clue_list:
            assert clue.context == ''.join(location_to_entry[location]
                                           for location in clue.locations)

        # Assert that the doubles are where they're supposed to be
        doubles2 = {location for location, value in location_to_entry.items()
                    if len(value) >= 2 and value.isupper()}
        doubles = [(q + 1, r + 1)
                   for delta in range(17)
                   for square in [(delta * 17 + 6 * 14 + 5) % 154]
                   for q, r in [divmod(square, 14)]]
        assert set(doubles) == doubles2

        # Make sure we really do get the words we're supposed to
        subtext = """ MAGICICADA CASSINI       SPHECIUS SPECIOSUS"""
        count1 = Counter(subtext)
        count1[' '] = 0
        count2 = Counter(x
                         for location in doubles
                         for pair in location_to_entry[location] for x in pair)
        assert count1 == count2

        for location in self.clue_named('21d').locations:
            temp = location_to_entry[location]
            location_to_entry[location] = str(ord(temp) - 64)

        for letter, location in zip("PREDATORSATIATION", doubles):
            location_to_entry[location] = letter

        super().draw_grid(location_to_entry=location_to_entry,
                          top_bars={}, left_bars={},
                          font_multiplier=.5,
                          coloring={x: 'blue' for x in doubles},
                          subtext=subtext,
                          **args)


if __name__ == '__main__':
    Junk.run()
