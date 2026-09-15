from collections import defaultdict
from collections.abc import Callable, Iterable
from typing import Unpack

from solver import (
    Clue,
    DancingLinksSolver,
    DrawGridKwargs,
    generators,
)

WORDS = {
    1: "SWEETMEAT",
    2: "MONOMETER",
    3: "NORMALISE",
    4: "MISALLIES",
    5: "MARCASITE",
    6: "MEDALISTS",
    7: "MONOTINTS",
    8: "RESENTING",
    9: "MILLIARES",
    10: "MYTILIDAE",
    11: "WISTERIAS",
    12: "INTERNIST",
    13: "RESISTING",
    14: "TOPIARIES",
    15: "ADIPOSITY",
    16: "FARMERIES",
    17: "MEMORISED",
    18: "ISLANDERS",
    19: "STONECOAL",
    20: "MISONEISM",
    21: "RIVERSIDE",
    22: "MEDITATED",
    23: "SANDHEAPS",
    24: "CASSEROLE",
    25: "POLEMISES",
    26: "GERMINATE",
    27: "AGITATION",
    28: "VANASPATI",
    29: "SEAANCHOR",
    30: "CHOPSOCKY",
}


def make_generator(word: str) -> Callable[[Clue], Iterable[str]]:
    assert len(word) == 9
    results: dict[str, None] = {}
    for i, first in enumerate(word):
        remainder = word[:i] + word[i + 1:]
        others = [remainder[j:] + remainder[:j] for j in range(8)]
        results.update((first + x, None) for x in others)
        results.update((first + x[::-1], None) for x in others)
    return generators.known(*results)


class Magpie285b(DancingLinksSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()
        solver.final_plot_board()

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues)
        self.grid = defaultdict(set)
        self.last_args = None

    def get_clues(self):
        clues = []
        for number in range(1, 31):
            row, column = divmod(number - 1, 5)
            row, column = (row + 1) * 2, (column + 1) * 2
            squares = [(row + dr, column + dc)
                       for dr, dc in [(0, 0), (-1, -1), (-1, 0), (-1, 1), (0, 1),
                                      (1, 1), (1, 0), (1, -1), (0, -1)]]
            clue = Clue(str(number), True, squares[0], length=9, locations=squares)
            if number in WORDS:
                clue.generator = make_generator(WORDS[number])
            clues.append(clue)
        return clues

    def draw_grid(self, **kwargs: Unpack[DrawGridKwargs]) -> None:
        self.last_args = kwargs
        grid = kwargs['location_to_entry']
        for location, value in grid.items():
            self.grid[location].add(value)

    def final_plot_board(self):
        kwargs = self.last_args
        grid = {location: ''.join(sorted(values)) for location, values in self.grid.items()
                if len(values) <= 5}
        kwargs['location_to_entry'] = grid
        kwargs['font_multiplier'] = .5
        (left_bars := kwargs['left_bars']).clear()
        (top_bars := kwargs['top_bars']).clear()
        for (r, c) in kwargs['location_to_clue_numbers']:
            left_bars.update(((r, c), (r, c + 1)))
            top_bars.update(((r, c), (r + 1, c)))
        super().draw_grid(**kwargs)


if __name__ == '__main__':
    Magpie285b.run()
