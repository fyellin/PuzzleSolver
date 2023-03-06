import collections
import itertools
import re
from functools import cache
from typing import Any

from solver import Clue, Clues, ConstraintSolver

GRID = """
XXX.X.X.XX
X....X....
.X...X....
X.....X...
...X.X....
XX.....XX.
X...X.....
X....X....
X.....X...
.X........
"""

ACROSS = [
    (1, 9),
    (8, 4),
    (9, 5),
    (10, 4),
    (11, 5),
    (12, 6),
    (13, 4),
    (15, 5),
    (16, 5),
    (20, 4),
    (21, 6),
    (22, 5),
    (23, 4),
    (24, 5),
    (25, 4),
    (26, 9)
]

DOWN = [
    (1, 10),
    (2, 5),
    (3, 5),
    (4, 9),
    (5, 6),
    (6, 5),
    (7, 10),
    (9, 9),
    (14, 6),
    (17, 5),
    (18, 5),
    (19, 5)
]

SET1 = """
    1a 0 COUNTRIES
    8a 2 SCUD
    9a 1 GIANT
    10a 2 COPY
    11a 0 LUGER
    12a 3 ANGLER
    13a 1 CHUM
    15a 1 WHOLE
    16a 1 CUMIN
    20a 0 GAZE
    21a 0 SPRINT
    22a 1 DRAIN
    23a 1 LOSE
    24a 1 OVERT
    25a 1 JAIL
    26a 1 DISLOCATE
    1d 1 DISCOURAGE
    2d 3 SURLY
    3d 1 COUNT
    4d 1 CREMATION
    5d 0 CHAPEL
    6d 3 CHUTE
    7d 0 CONFIGURED
    9d 1 STRANGELY
    14d 0 CINEMA
    17d 2 MATZO
    18d 0 PETAL
    19d 0 LOADS
"""

SET2 = """
    1a 2 GOLDSMITH
    8a 2 TORY
    9a 1 PIQUE
    10a 0 DIAL
    11a 3 SCENT
    12a 0 GROUND
    13a 1 APEX
    15a 0 FLOUR
    16a 1 DORKY
    20a 1 PELT
    21a 0 RADISH
    22a 0 FACET
    23a 0 BLUR
    24a 3 MORAL
    25a 0 EDGY
    26a 1 CRUSADING
    1d 2 FORMULATED
    2d 0 SLOTH
    3d 2 DRAWL
    4d 2 HAIRSTYLE
    5d 1 SUPLEX
    6d 1 GRAIN
    7d 3 REGULATION
    9d 0 ALONGSIDE
    14d 0 CAVORT
    17d 1 DUPER
    18d 1 BRINY
    19d 1 CUBED
"""


class Magpie243b(ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie243b()
        # solver.plot_board()
        # solver.verify_is_180_symmetric()
        solver.fill_grid()

    def __init__(self):
        clues = []
        locations = Clues.get_locations_from_grid(GRID)
        for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd')):
            for (number, length) in lines:
                location = locations[number - 1]
                clue = Clue(f'{number}{letter}', is_across, location, length)
                clues.append(clue)
        super().__init__(clues)

    def fill_grid(self):
        dones = {}
        for which in (2, 1):
            word_info = self.get_info(which)
            previous_done = dones[2] if which == 1 else None
            dones[which] = self.handle(word_info, previous_done)
            print(previous_done)

        plotter = {location: dones[1][location] + dones[2][location]
                   for location in itertools.product(range(1, 11), repeat=2)}
        self.plot_board({}, plotter=plotter)

    def handle(self, word_info, other_done=None):
        word_info = {clue: info for clue, (_, info) in word_info.items()}
        locations = collections.defaultdict(list)
        for clue in word_info.keys():
            for i, location in enumerate(clue.locations):
                locations[location].append((clue, i))
        done = {}
        if other_done:
            for location, letter in other_done:
                for clue, index in locations[location]:
                    if clue in word_info:
                        word_info[clue] = [x for x in word_info[clue]
                                           if x[index] != letter]

        def handle_one_location(location):
            if location in done:
                return
            if not (location_info := locations[location]):
                return

            target = handle_intersection(location_info)
            if len(target) == 1:
                letter = next(iter(target))
                done[location] = letter
                handle_singleton(location, letter)

        def handle_intersection(location_info):
            nonlocal changed
            values = [{word[index] for word in word_info[clue]}
                      for clue, index in location_info]
            result = set.intersection(*values)
            for clue, index in location_info:
                old_value = word_info[clue]
                new_value = [x for x in old_value if x[index] in result]
                if len(old_value) > len(new_value):
                    print(f'{location} {clue.name:<3} {len(old_value)} -> {len(new_value)}')
                    word_info[clue] = new_value
                    changed = True
            return result

        def handle_singleton(location, letter):
            nonlocal changed
            print(f'{location} = {letter}')
            clues = {clue for clue, _index in locations[location]}
            row, column = location
            for location2 in [(row, i) for i in range(1, 11)] + \
                             [(i, column) for i in range(1, 11)]:
                if location == location2:
                    continue
                for clue2, index2 in locations[location2]:
                    if clue2 in clues:
                        continue
                    old_value = word_info[clue2]
                    new_value = [x for x in old_value if x[index2] != letter]
                    if len(old_value) > len(new_value):
                        print(f'{location} {clue2.name:<3} {len(old_value)} -> {len(new_value)}')
                        word_info[clue2] = new_value
                        changed = True

        for counter in itertools.count(1):
            print(f"Starting round {counter}")
            changed = False
            for location in itertools.product(range(1, 11), repeat=2):
                handle_one_location(location)

            if not changed or len(done) == 100:
                break

        return done

    def draw_grid(self, plotter=None, **args: Any) -> None:
        if plotter:
            args |= dict(location_to_entry=plotter)
        super().draw_grid(**args, font_multiplier=.5)

    def get_info(self, which):
        result = {}

        for line in (SET1 if which == 1 else SET2).splitlines():
            if not line:
                continue
            match = re.fullmatch(r'(\d+[ad]) (\d) (.+)', line.strip())
            word = match.group(3)
            if word == '*':
                continue
            clue = self.clue_named(match.group(1))
            same = int(match.group(2))
            assert len(word) == clue.length
            info = permute(word, same)
            result[clue] = word, info
        return result


@cache
def get_permutations(n):
    results = [list() for _ in range(n + 1)]
    for permutation in itertools.permutations(range(n)):
        same = sum(i == b for i, b in enumerate(permutation))
        results[same].append(permutation)
    return results


def permute(word, same):
    permutations = get_permutations(len(word))[same]
    return [''.join(word[i] for i in permutation) for permutation in permutations]


def foo():
    count = 0
    items = ('[osu]', '[^sucdgaitnh]', '[^ielrug]', 'e', '[^umelhweo]', 'n', 't', 'i', 'r' )
    # items = 'y', 'o', '[^udgmcane]', 'c'
    same = 1
    length = len(items)

    permutations = get_permutations(length)[same]
    info = [''.join(items[i] for i in permutation) for permutation in permutations]
    info = re.compile('|'.join(info))
    print(info)
    with open("../misc/words.txt", "r") as file:
        for real_word in file:
            real_word = real_word.strip()
            word = real_word.replace('-', '').lower()
            if len(word) == length and len(set(word)) == length and re.fullmatch(r'\w+', word):
                if info.fullmatch(word):
                    print(real_word)
                    count += 1

        print(count)


if __name__ == '__main__':
    foo()
    # Magpie243b.run()


