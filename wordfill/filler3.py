import copy
import functools
import importlib
import itertools
import pickle
import sys
from collections import deque
from typing import Sequence, Dict, List, Tuple, Deque, cast, Set, Any, Callable, FrozenSet

Location = Tuple[int, int]

WORDS1 = ("abs", "ace",
          "ghost",
          "abdomen", "brosnan", "courage", "dungeon", "madonna", "neatens", "suntans",
          )
WORDS2 = ("kit", "wax",
          "entia",
          "undies",
          "anodyne", "interse", "oysters", "poverty", "thyrsus", "wipeout",
          "icedancer",
          )
WORDS3 = ("edh", "key",
          "elvira",
          "adherer", "beastie", "oldhand", "tasered",
          "unshackle",
          )
WORDS4 = ("rad", "use",
          "thete",
          "athene",
          "appends", "papilla", "resolve", "scalier", "spotter",
          "littleowl",
         )


GRID_SIZE = 7

class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    slice: Any
    locations: Sequence[Location]

    def __init__(self, is_across: bool, start_location: Location, length: int) -> None:
        (row, column) = start_location
        name = f"({row},{column}):{length}:{'A' if is_across else 'D'}"
        self.name = name
        self.is_across = is_across
        self.base_location = start_location
        self.length = length
        slice_start = (row - 1) * GRID_SIZE + (column - 1)
        if self.is_across:
            self.slice = slice(slice_start, slice_start + self.length, 1)
            self.locations = tuple((row, column + i) for i in range(length))
        else:
            self.slice = slice(slice_start, slice_start + self.length * GRID_SIZE, GRID_SIZE)
            self.locations = tuple((row + i, column) for i in range(length))

    @functools.lru_cache(maxsize=None)
    def to_solver_clue(self) -> Any:
        return cast(Any, self)

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Clue):
            return NotImplemented
        return self.name == other.name

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)

    @staticmethod
    def all_of_length_n(length: int) -> Sequence['Clue']:
        result = []
        for i in range(1, GRID_SIZE + 1):
            for j in range(1, GRID_SIZE + 1 - (length - 1)):
                if length != 9 or i != 1:
                    result.append(Clue(True, (i, j), length))
                if length != 9:
                    result.append(Clue(False, (j, i), length))
        return tuple(result)




class Solver:
    words: Sequence[str]
    results: List[Tuple[str, Clue]]
    allocated_locations: List[int]
    grid: List[str]
    counter: int


    def __init__(self) -> None:
        words = sorted(WORDS1, key=len, reverse=True)
        self.words = tuple(words)
        self.results = []
        self.grid = ['.'] * (GRID_SIZE * GRID_SIZE)
        self.allocated_locations = [0] * (GRID_SIZE * GRID_SIZE)
        self.counter = 0

    def run(self, index: int) -> None:
        if index >= len(self.words):
            if self.allocated_locations.count(3) >= 10:
                self.print_me()
            return

        # if self.counter >= 1_000_000:
        #     sys.exit(0)
        #
        word = self.words[index]
        self.try_at_all_locations(index, word, len(word))


    def try_at_all_locations(self, index: int, word: str, word_length: int) -> None:
        saved_allocated_locations = list(self.allocated_locations)
        possible_clues = Clue.all_of_length_n(word_length)
        for clue in possible_clues:
            bit = 1 if clue.is_across else 2
            temp = self.allocated_locations[clue.slice]
            if all(x & bit == 0 for x in temp):
                self.allocated_locations[clue.slice] = [x | bit for x in temp]
                self.try_word_at_location(index, word, word_length, clue)
                self.allocated_locations[clue.slice] = temp
        assert saved_allocated_locations == self.allocated_locations

    MAX_SHOW = 12

    def try_word_at_location(self, index: int, word: str, word_length: int, this_clue: Clue) -> None:
        self.counter += 1

        grid = self.grid
        clue_slice = this_clue.slice
        saved_grid = grid[clue_slice]


        for x, y in zip(saved_grid, word):
            if x != '.' and x != y:
                return None

        self.results.append((word, this_clue))
        grid[clue_slice] = word
        if index < self.MAX_SHOW:
                print(f'{" | " * index}{word} {this_clue} {self.counter:,} =>')
        self.run(index + 1)
        grid[clue_slice] = saved_grid
        self.results.pop()

    def print_me(self) -> None:
        module = importlib.import_module("solver")
        all_clues = []
        for _, clue in self.results:
            all_clues.append(clue)

        solver_clues = [clue.to_solver_clue() for clue in all_clues]
        solver_dict = {clue.to_solver_clue(): word for (word, clue) in self.results}

        class MySolver (module.BaseSolver):
            def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                          location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
                          top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:
                location_to_clue_number.clear()
                super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                                  top_bars, left_bars, **more_args)

            def solve(self, *, show_time: bool = True, debug: bool = False) -> int: ...

        MySolver(solver_clues).plot_board(solver_dict)

if __name__ == '__main__':
    solver = Solver()
    solver.run(0)
