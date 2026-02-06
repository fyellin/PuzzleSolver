import itertools
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass

START_GRID = """
.G..RE...
....A.P.A
S.A.I...N
.ACB.I..S
.E...T..S
T...A..R.
.T....EC.
.RR....E.
..FS.A..S
"""

BAD_COLUMNS = (1, 5,)
ACROSSES = ["REGICIDES", "APPERTAIN", "SCENARIOS", "ALBICORES", "SNOTTIEST",
            "REAGANITE", "CORNETIST", "REENTRANT", "SASSAFRAS"]

DOWNS = ["ACRNST", "GRAPETREE", "FRICASSEE", "BARRISTER",
         "ASORIE", "ATTENTION", "PINNACLED", "CROSSTIES", "STAGINESS"]

PAIRS = [
    ("APERIENTS", "EPISTERNA"),
    ("CESSATION", "CANOEISTS"),
    ("RESIANCES", "INCREASES"),
    ("NEARSIDES", "DRAISENES"),
    ("NECROTISE", "ERECTIONS"),
    ("STEARINES", "RESINATES"),
    ("TARRINESS", "STRAINERS"),
    ("TRITENESS", "INSETTERS"),
]

def get_start_grid():
    grid = {}
    for row, col in itertools.product(range(1, 10), repeat=2):
        if col not in BAD_COLUMNS:
            grid[row, col] = set(ACROSSES[row - 1]).intersection(DOWNS[col - 1])
        else:
            grid[row, col] = set(ACROSSES[row - 1])
    for rc in range(1, 10):
        grid[rc, 0] = Counter(ACROSSES[rc - 1])
        grid[0, rc] = Counter(DOWNS[rc - 1])

    lines = START_GRID.strip().splitlines()
    for row, line in enumerate(lines, start = 1):
        for col, letter in enumerate(line, start = 1):
            if letter != '.':
                set_grid(grid, row, col, letter)
    for word1, word2 in PAIRS:
        assert Counter(word1) == Counter(word2)
        for letter, count in Counter(word1).items():
            if count == 1:
                row = word2.index(letter) + 1
                col = word1.index(letter) + 1
                if isinstance(grid[row, col], set):
                    assert letter in grid[row, col]
                    set_grid(grid, row, col, letter)
                else:
                    assert grid[row, col] == letter
    return grid

def set_grid(grid, row, col, letter):
    assert letter in grid[row, col]
    assert grid[row, 0][letter] > 0
    assert grid[0, col][letter] > 0 or col in BAD_COLUMNS
    grid[row, col] = letter
    grid[row, 0][letter] -= 1
    if grid[row, 0][letter] == 0:
        grid[row, 0].pop(letter)
        for c in range(1, 10):
            if isinstance(grid[row, c], set):
                grid[row, c].discard(letter)
    grid[0, col][letter] -= 1
    if grid[0, col][letter] <= 0:
        grid[0, col].pop(letter)
        if col not in BAD_COLUMNS:
            for r in range(1, 10):
                if isinstance(grid[r, col], set):
                    grid[r, col].discard(letter)

def fix_singletons(grid):
    fixes = []
    for (row, col), value in grid.items():
        if row > 0 and col > 0 and isinstance(value, set) and len(value) == 1:
            fixes.append((row, col, next(iter(value))))
    for (row, col, letter) in fixes:
            set_grid(grid, row, col, letter)
    return bool(fixes)

def fix_requires(grid):
    return False
    fixes = set()
    for row in range(1, 10):
        for letter, count in grid[row, 0].items():
            assert count > 0
            places = [col for col in range(1, 10) if isinstance(grid[row, col], set) and letter in grid[row, col]]
            assert len(places) >= count
            if len(places) == count:
                fixes.update((row, c, letter) for c in places)
    for col in range(1, 10):
        for letter, count in grid[0, col].items():
            assert count > 0
            places = [row for row in range(1, 10) if isinstance(grid[row, col], set) and letter in grid[row, col]]
            assert len(places) >= count
            if len(places) == count:
                fixes.update((r, col, letter) for r in places)
    for (row, col, letter) in fixes:
            set_grid(grid, row, col, letter)
    return bool(fixes)


def print_grid(grid):
    output = {}
    for (row, col), value in grid.items():
        if row > 0 and col > 0:
            if isinstance(value, str):
                assert len(value) == 1
                output[row, col] = value
            else:
                output[row, col] = ''.join(sorted(value)).lower()
        else:
            output[row, col] = ''.join(sorted(value.elements()))
            if col in BAD_COLUMNS and output[row, col]:
                output[row, col] = '(' + output[row, col] + ')'
    max_length = max(len(x) for x in output.values()) + 1
    for row in range(1, 10):
        for col in range(1, 10):
            print(f'{output[row, col]:{max_length}}', end='')
        print('|', output[row, 0])
    print('-' * (max_length * 10))
    for col in range(1, 10):
        print(f'{output[0, col]:{max_length}}', end='')
    print(); print()

def runner():
    grid = get_start_grid()
    print_grid(grid)
    while (fix_singletons(grid) or fix_requires(grid)):
        pass
    print_grid(grid)

    result = [
        ''.join(grid[row, col] for col in range(1, 10)) for row in range(1, 10)
    ]
    print(result)


    # for word1, word2 in PAIRS:
    #     print(word1, word2)
    #     for letter, count in Counter(word1).items():
    #         if count > 1:
    #             cols = [index for index, ch in enumerate(word1, start=1) if ch == letter]
    #             rows = [index for index, ch in enumerate(word2, start=1) if ch == letter]
    #             print('  ', rows, cols)
    #             rc = [loc for loc in itertools.product(rows, cols) if grid[loc] == letter]
    #             print('    ', rc)

if __name__ == '__main__':
    runner()


