from __future__ import annotations

import re
from typing import Sequence, Tuple, List

from .clue import Clue
from .clue_types import Location


class Clues:
    @staticmethod
    def get_locations_from_grid(grid: str) -> Sequence[Location]:
        grid = grid.strip()
        return [(row + 1, column + 1)
                for row, line in enumerate(grid.splitlines())
                for column, item in enumerate(line)
                if item == 'X']

    @classmethod
    def create_from_text(cls, across: str, down: str, locations: Sequence[Tuple[int, int]]) -> Sequence[Clue]:
        result: List[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=match.group(2))
                result.append(clue)
        return result
