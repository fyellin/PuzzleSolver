import string
from collections import defaultdict
from collections.abc import Hashable, Sequence

from more_itertools.more import distinct_permutations

from solver import (
    Clue,
    ConstraintSolver,
    DancingLinks,
    DancingLinksBounds,
    DLConstraint,
)
from solver.dancing_links import get_row_column_optional_constraints

SQUARES = [
    None,
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 6), (1, 7), (1, 8), (1, 9), (1, 10), (1, 11), (1, 12),
    (2, 1), (2, 5), (2, 8), (2, 11), (2, 13),
    (3, 1), (3, 4), (3, 7),
    (4, 1), (4, 6), (4, 7), (4, 13),
    (5, 1), (5, 6), (5, 9), (5, 10), (5, 11), (5, 13),
    (6, 1), (6, 3), (6, 4), (6, 8), (6, 9),
    (7, 1), (7, 7), (7, 13),
    (8, 2), (8, 5), (8, 8), (8, 9), (8, 10), (8, 12),
    (9, 1), (9, 5), (9, 6), (9, 7), (9, 10), (9, 12),
    (10, 1), (10, 3), (10, 4), (10, 6), (10, 8), (10, 9), (10, 11),
    (11, 2), (11, 8), (11, 12), (11, 13),
    (12, 1), (12, 3), (12, 5),
    (13, 1), (13, 8),
]

COLORS = """
YYYYYYRRRRGGG
YRRRGGGRRRGGG
YRGRRGGGGBYGG
YGGYYYYYGBYYY
GGGYYGRYBBYYG
GRRYGGRRRBGYG
RRRGGYYRRBGGG
RRGGGYYYGGYYY
YYYRRBBYGGGYY
YYYRYYBBGGBBY
GGRRRYBGGBBBR
GGGYRYBBGBBRR
GGGYYYBRRRRRR
"""

ACROSS_CLUES = {
    3: "IFTAR",
    7: "ANDREW",
    12: "MURICES",
    14: "HALLS",
    17: "EARNED",
    19: "POTTERY",
    20: "BENNET",
    22: "GASSIER",
    24: "MANDALA",
    26: "TILT",
    31: "SPINET",
    34: "URDEE",
    35: "ANGLE",
    36: "STEALTH",
    38: "PLOVER",
    42: "TOEA",
    44: "HART",
    45: "SUBMIT",
    50: "BIREME",
    55: "MODEM",
    57: "NICEST",
    58: "TONDO",
    61: "USE",
    63: "LITTLEMAN",
    64: "STIMIE",
    65: "ENROLL",
}

DOWN_CLUES = {
    1: "BEGAN",
    2: "MURDER",
    3: "MASCAGNI",
    4: "TURNS",
    5: "KIEV",
    6: "CARLINE",
    7: "WHOSE",
    8: "STATUA",
    9: "LENT",
    10: "LEAD",
    11: "BURGERS",
    13: "VOIDEES",
    16: "RICEY",
    25: "BEAN",
    27: "IDLE",
    28: "LEEAR",
    30: "MAIA",
    32: "PLOD",
    33: "ATOM",
    37: "HERMIT",
    38: "PRINT",
    41: "CIMIER",
    43: "FOETAL",
    45: "SEETO",
    46: "UMAMI",
    47: "MOTIF",
    48: "POOL",
    50: "MAUI",
    51: "ETHE",
    52: "FIRS",
    54: "NEON",
    56: "MILO",
}

SHAPE_CLUES = {
    9: "NARWHAL",
    13: "SOLSTICE",
    15: "LYREBIRD",
    20: "BATTERING",
    21: "VILIPENDS",
    23: "REGULAR",
    24: "ANAEMIA",
    26: "TITLED",
    29: "CHEESE",
    33: "ATTUNE",
    38: "PAUSING",
    39: "VOCALION",
    40: "TAMBRE",
    45: "SHIFTER",
    47: "MOUNTING",
    49: "OMERTA",
    50: "BARITE",
    53: "MISTIMES",
    58: "OCTODECIMO",
    59: "TOLLMEN",
    60: "PATROLLER",
    62: "HUMANISE"
}


class Magpie208b(ConstraintSolver):
    constraints: dict[Hashable, list[DLConstraint]]
    optional_constraints: set[str]
    segments: Sequence[set[tuple[int, int]]]
    segments_map: dict[tuple[int, int], set[tuple[int, int]]]

    @classmethod
    def run_me(cls):
        solver = cls()
        solver.dl_solve()

    def __init__(self):
        self.constraints: dict[Hashable, list[DLConstraint]] = {}
        self.optional_constraints: set[str] = get_row_column_optional_constraints(13, 13)
        # self.optional_constraints |= {x + "-misprint" for x in self.optional_constraints}
        self.bounds = {}
        self.colors = self.read_colors()
        self.segments = self.get_segments(self.colors)
        self.segments_map = {
            location: segment for segment in self.segments for location in segment
        }
        clues = self.get_clues()
        self.clue_map = {clue.name: clue for clue in clues}
        super().__init__([x for x in clues if not x.name.endswith('s')])

    def get_clues(self) -> list[Clue]:
        clues = []
        for is_across, info, letter in ((True, ACROSS_CLUES, 'a'), (False, DOWN_CLUES, 'd')):
            for number, value in info.items():
                clues.append(Clue(f'{number}{letter}', is_across, SQUARES[number], len(value)))

        for number, value in SHAPE_CLUES.items():
            start = SQUARES[number]
            segment = self.segments_map[start]
            assert len(segment) == len(value)
            locations = [start, *sorted(segment - {start})]
            clues.append(Clue(f'{number}s', True, start, len(segment),
                         locations=locations))
        return clues

    def dl_solve(self):
        self.handle_strips()
        self.handle_across_down_clues(True)
        self.handle_across_down_clues(False)

        # solution = [(self.clue_map[x[0]], x[1], x[2], x[3]) for x in SOLUTION]
        # verify_solution(solution, self.constraints, self.optional_constraints, self.bounds)

        if self.bounds:
            function, kwargs = DancingLinksBounds, {"bounds": self.bounds}
        else:
            function, kwargs = DancingLinks, {}
        solver = function(self.constraints,
                          optional_constraints=self.optional_constraints,
                          row_printer=self.show_solution, **kwargs)
        solver.solve(debug=True, max_debug_depth=100)

    def handle_across_down_clues(self, is_across: bool):
        if is_across:
            letter, rc_literal, clues, index = 'a', "Row", ACROSS_CLUES, 0
        else:
            letter, rc_literal, clues, index = 'd', "Column", DOWN_CLUES, 1

        clues_in_row_column = defaultdict(list)

        for number, value in clues.items():
            clue = self.clue_map[f'{number}{letter}']
            rc = clue.base_location[index]
            clues_in_row_column[rc].append(clue)
            anagrams = [p for x in distinct_permutations(value)
                        if (p := ''.join(x)) != value]
            misprints = [value[:index] + char2 + value[index + 1:]
                         for index, char in enumerate(value)
                         for char2 in string.ascii_uppercase
                         if char != char2]
            for xtype, variants in (('anagram', anagrams), ('misprint', misprints)):
                for p in variants:
                    self.constraints[('clue', clue.name), value, p, xtype] = [
                        f'clue-{clue.name}',
                        f'{rc_literal}-{rc}-{xtype}',
                        *clue.dancing_links_rc_constraints(p),
                    ]

        for rc, clues in clues_in_row_column.items():
            if len(clues) >= 3:
                for xtype in ('anagram', 'misprint'):
                    self.bounds[f'{rc_literal}-{rc}-{xtype}'] = (1, 2)

    def handle_strips(self):
        constraints = self.constraints
        # Give this row a unique constraint so that it is forced.
        first_letter_constraint: list[DLConstraint] = ['FIRST_LETTERS_STRIP_FIXED']
        for number, value in SHAPE_CLUES.items():
            clue = self.clue_map[f'{number}s']
            (r, c) = clue.location(0)
            first_letter_constraint.append((f'r{r}c{c}', value[0]))
            permutations = [value[0] + ''.join(x) for x in distinct_permutations(value[1:])]
            for p in permutations:
                constraints[('clue', clue.name), value, p, 'anagram'] = [
                    f'clue-{clue.name}',
                    *clue.dancing_links_rc_constraints(p)]
        constraints["FIRST_LETTER_STRIP_FIXED"] = first_letter_constraint

    def show_solution(self, solution):
        print(solution)
        all_clues = {}
        misprints = []
        for item in solution:
            match item:
                case (('clue', name), original, entered, ctype):
                    clue = self.clue_map[name]
                    all_clues[clue] = entered
                    if ctype == 'misprint':
                        location = next(clue.location(i)
                                        for i, (c1, c2) in enumerate(zip(original, entered, strict=True))
                                        if c1 != c2)
                        misprints.append(location)
        normal_clues = {clue: value for clue, value in all_clues.items()
                        if not clue.name.endswith('s')}

        circled = {location for location in misprints if self.colors[location] == 'lightgreen'}
        super().plot_board(normal_clues, font_multiplier=.8, shading=self.colors, circles=circled)

    def read_colors(self) -> dict[tuple[int, int], str]:
        color_map = {"R": "coral", "G": "lightgreen", "B": "lightblue", "Y": "yellow"}
        colors = {}
        for row, line in enumerate(COLORS.strip().splitlines(), start=1):
            for col, char in enumerate(line, start=1):
                colors[row, col] = color_map[char]
        return colors

    def get_segments(self, color_map: dict[tuple[int, int], str]) -> Sequence[set[tuple[int, int]]]:
        segments = []
        color_map = color_map.copy()
        while color_map:
            this_segment = [min(color_map.keys())]
            this_color = color_map.pop(this_segment[0])
            i = 0
            while i < len(this_segment):
                r, c = this_segment[i]
                i += 1
                for dr, dc in (-1, 0), (1, 0), (0, -1), (0, 1):
                    (r2, c2) = (r + dr, c + dc)
                    if color_map.get((r2, c2)) == this_color:
                        this_segment.append((r2, c2))
                        color_map.pop((r2, c2))
            segments.append(set(this_segment))
        return segments


SOLUTION = [
    ('3a', 'IFTAR', 'ITTAR', 'misprint'),
    ('7a', 'ANDREW', 'WANDER', 'anagram'),
    ('12a', 'MURICES', 'ERMUSIC', 'anagram'),
    ('14a', 'HALLS', 'HALLB', 'misprint'),
    ('17a', 'EARNED', 'NDAREE', 'anagram'),
    ('19a', 'POTTERY', 'LOTTERY', 'misprint'),
    ('20a', 'BENNET', 'BENNEV', 'misprint'),
    ('22a', 'GASSIER', 'ISSEAGR', 'anagram'),
    ('24a', 'MANDALA', 'AMALDAN', 'anagram'),
    ('26a', 'TILT', 'TILU', 'misprint'),
    ('31a', 'SPINET', 'SPINEA', 'misprint'),
    ('34a', 'URDEE', 'UDERE', 'anagram'),
    ('35a', 'ANGLE', 'ANGLO', 'misprint'),
    ('36a', 'STEALTH', 'ATTLESH', 'anagram'),
    ('38a', 'PLOVER', 'PCOVER', 'misprint'),
    ('42a', 'TOEA', 'OATE', 'anagram'),
    ('44a', 'HART', 'ARTH', 'anagram'),
    ('45a', 'SUBMIT', 'SUMMIT', 'misprint'),
    ('50a', 'BIREME', 'BIEREM', 'anagram'),
    ('55a', 'MODEM', 'MOMEM', 'misprint'),
    ('57a', 'NICEST', 'NIFEST', 'misprint'),
    ('58a', 'TONDO', 'ODONT', 'anagram'),
    ('61a', 'USE', 'USH', 'misprint'),
    ('63a', 'LITTLEMAN', 'TMINELLAT', 'anagram'),
    ('64a', 'STIMIE', 'IMESTI', 'anagram'),
    ('65a', 'ENROLL', 'ERROLL', 'misprint'),
    ('1d', 'BEGAN', 'GENBA', 'anagram'),
    ('2d', 'MURDER', 'RRDEMU', 'anagram'),
    ('3d', 'MASCAGNI', 'IMANASGC', 'anagram'),
    ('4d', 'TURNS', 'TURNL', 'misprint'),
    ('5d', 'KIEV', 'AIEV', 'misprint'),
    ('6d', 'CARLINE', 'RCLINEA', 'anagram'),
    ('7d', 'WHOSE', 'WHOSI', 'misprint'),
    ('8d', 'STATUA', 'AATSTU', 'anagram'),
    ('9d', 'LENT', 'NLTE', 'anagram'),
    ('10d', 'LEAD', 'DLEA', 'anagram'),
    ('11d', 'BURGERS', 'EBRGURS', 'anagram'),
    ('13d', 'VOIDEES', 'SEEDIOV', 'anagram'),
    ('16d', 'RICEY', 'IYRCE', 'anagram'),
    ('25d', 'BEAN', 'ANBE', 'anagram'),
    ('27d', 'IDLE', 'IDLO', 'misprint'),
    ('28d', 'LEEAR', 'LEEAC', 'misprint'),
    ('30d', 'MAIA', 'IAIA', 'misprint'),
    ('32d', 'PLOD', 'PLOH', 'misprint'),
    ('33d', 'ATOM', 'ATTM', 'misprint'),
    ('37d', 'HERMIT', 'HERMPT', 'misprint'),
    ('38d', 'PRINT', 'PRINS', 'misprint'),
    ('41d', 'CIMIER', 'CIMDER', 'misprint'),
    ('43d', 'FOETAL', 'TOETAL', 'misprint'),
    ('45d', 'SEETO', 'SEETT', 'misprint'),
    ('46d', 'UMAMI', 'UMSMI', 'misprint'),
    ('47d', 'MOTIF', 'MOTIG', 'misprint'),
    ('48d', 'POOL', 'TOOL', 'misprint'),
    ('50d', 'MAUI', 'BAUI', 'misprint'),
    ('51d', 'ETHE', 'EIHE', 'misprint'),
    ('52d', 'FIRS', 'RFIS', 'anagram'),
    ('54d', 'NEON', 'NONE', 'anagram'),
    ('56d', 'MILO', 'MNLO', 'misprint'),
    ('9s', 'NARWHAL', 'NRWAHAL', 'anagram'),
    ('13s', 'SOLSTICE', 'SICELOTS', 'anagram'),
    ('15s', 'LYREBIRD', 'LDERBIRY', 'anagram'),
    ('20s', 'BATTERING', 'BGRITTAEN', 'anagram'),
    ('21s', 'VILIPENDS', 'VNEISLDIP', 'anagram'),
    ('23s', 'REGULAR', 'REAGLUR', 'anagram'),
    ('24s', 'ANAEMIA', 'AAENMAI', 'anagram'),
    ('26s', 'TITLED', 'TTEIDL', 'anagram'),
    ('29s', 'CHEESE', 'CEEESH', 'anagram'),
    ('33s', 'ATTUNE', 'ANEUTT', 'anagram'),
    ('38s', 'PAUSING', 'PUSANGI', 'anagram'),
    ('39s', 'VOCALION', 'VAINLOCO', 'anagram'),
    ('40s', 'TAMBRE', 'TBAERM', 'anagram'),
    ('45s', 'SHIFTER', 'SHRIFET', 'anagram'),
    ('47s', 'MOUNTING', 'MUONTING', 'anagram'),
    ('49s', 'OMERTA', 'OATERM', 'anagram'),
    ('50s', 'BARITE', 'BARTIE', 'anagram'),
    ('53s', 'MISTIMES', 'MESIMSTI', 'anagram'),
    ('58s', 'OCTODECIMO', 'OCOITCMODE', 'anagram'),
    ('59s', 'TOLLMEN', 'TMEONLL', 'anagram'),
    ('60s', 'PATROLLER', 'PATERROLL', 'anagram'),
    ('62s', 'HUMANISE', 'HANUSIME', 'anagram'),
]


if __name__ == '__main__':
    Magpie208b.run_me()
