from __future__ import annotations

import re
from collections.abc import Sequence

from .clue import Clue
from .clue_types import Location


class Clues:
    @staticmethod
    def get_locations_from_grid(grid: str) -> Sequence[Location]:
        grid = grid.strip()
        return [(row + 1, column + 1)
                for row, line in enumerate(grid.splitlines())
                for column, item in enumerate(line)
                if item.upper() == 'X']

    @classmethod
    def create_from_text(cls, across: str, down: str, locations: Sequence[Location]|str) -> Sequence[Clue]:
        if isinstance(locations, str):
            locations = Clues.get_locations_from_grid(locations)
        result: list[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                if not match:
                    raise ValueError(f'Cannot create a match from "{line}"')
                number = int(match.group(1))
                location = locations[number - 1]
                clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=match.group(2).strip())
                result.append(clue)
        return result

    @classmethod
    def create_from_text2(cls, across: str, down: str, across_lengths: str, down_lengths: str) -> Sequence[Clue]:
        all_clue_info = cls.clue_info_from_clue_sizes(across_lengths, down_lengths)
        result: list[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*)', line)
                if not match:
                    raise ValueError(f'Cannot create a match from "{line}"')
                number = int(match.group(1))
                try:
                    name, location, length = all_clue_info.pop((number, is_across))
                except KeyError:
                    print(f'Cannot find a clue {number}{across}')
                    continue
                clue = Clue(f'{number}{letter}', is_across, location, length,
                            expression=match.group(2).strip())
                result.append(clue)
        if all_clue_info:
            for (number, is_across) in all_clue_info:
                print(f"No information given for clue {number}{"a" if is_across else "d"}")
        return result


    @classmethod
    def clues_from_clue_sizes(cls, across, down):
        info = cls.clue_info_from_clue_sizes(across, down)
        return [Clue(name, is_across, location, length)
                for (number, is_across), (name, location, length) in info.items()]

    @staticmethod
    def clue_info_from_clue_sizes(across, down) -> dict[tuple[int, bool], [str, tuple[int, int], int]]:
        clues = []
        starts = set()
        for is_across, info in (True, across), (False, down):
            for x, row_info in enumerate(info.split('/'), start=1):
                y = 1
                for length in [int(x) for x in list(row_info)]:
                    if length != 1:
                        location = (x, y) if is_across else (y, x)
                        clues.append((is_across, location, length))
                        starts.add(location)
                    y += length
        starts = {start: index for index, start in enumerate(sorted(starts), start=1)}
        return {(starts[location], is_across) : (name, location, length)
                for is_across, location, length in clues
                for name in [f'{starts[location]}{"a" if is_across else "d"}']}
