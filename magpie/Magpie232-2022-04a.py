import itertools
import re

from solver import DancingLinks
from solver.dancing_links import get_row_column_optional_constraints
from solver.draw_grid import draw_grid


def build_table(is_row, row, *words):
    locations = [(row, i) if is_row else (i, row) for i in range(1, 14)]
    extra = 13 - sum(len(word) for word in words)
    if len(words) == 1:
        word1, = words
        keys = [word1 + ('.' * extra)]
    else:
        word1, word2 = words
        keys = [word1 + '.' * i + word2 + '.' * (extra - i) for i in range(0, extra + 1)]

    results = [{loc: letter for loc, letter in zip(locations, key[i:] + key[:i])
                if letter != '.'}
               for key in keys for i in range(13)]
    return results


CLUES = """
6a. oregon mail
10a. contralto urge
11a. omasa brooded
12a. send badges
13a. mutant steins
1d. agaric rodsman
2d. hidalgo gnetum
8d. parastatal
10d. ortolan telugu
11d. octodecimal
3a. sienna
4a. rifle
7a. yeard
3d. oedema
7d. informal
12d. cossies
13d. amateur
"""


def get_info():
    result = {}
    for line in CLUES.strip().splitlines():
        match = re.match(r"(\d+)([ad])\. (.*)", line)
        number = int(match.group(1))
        is_across = match.group(2) == 'a'
        words = match.group(3).split(' ')
        result[f"{number}{match.group(2)}"] = build_table(is_across, number, *words)
    return result


def main2():
    constraints = {}
    optional_constraints = get_row_column_optional_constraints(13, 13)
    for row_name, rows in get_info().items():
        is_across = row_name[-1] == 'a'
        for row in rows:
            letter_info = [(f"r{r}c{c}", letter)
                           for (r, c), letter in row.items()]
            constraints[tuple(row.items())] = [row_name, *letter_info]
    runner = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=printer)
    runner.solve()


def printer(results):
    results = {location: value.upper()
               for result in results for location, value in result}
    draw_grid(max_row=14, max_column=14, location_to_entry=results, font_multiplier=.7)


if __name__ == '__main__':
    main2()
