import functools
import sys
from typing import Sequence, Dict, Set, List, Tuple


# from solver import Clue as SolverClue, ConstraintSolver

Location = Tuple[int, int]

WORDS = ("abs", "ace",
         "ghost",
         "abdomen", "brosnan", "courage", "dungeon", "madonna", "neatens", "suntans",
         "kit", "wax",
         "entia",
         "undies",
         "anodyne", "inter se", "oysters", "poverty", "thyrsus", "wipe out",
         "ice dancer",
         "edh", "key",
         "elvira",
         "adherer", "beastie", "old hand", "tasered",
         "unshackle",
         "rad", "use",
         "thete",
         "athene",
         "appends", "resolve", "scalier", "spotter",
         "little owl",
         )


class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    my_slice: slice

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_quad(start_location: Location, length: int) -> Sequence['Clue']:
        row1, column1 = start_location      # start location
        row2, column2 = column1, 15 - row1  # start location stays start location
        row3, column3 = column2, 15 - row2 - (length - 1)
        row4, column4 = column3, 15 - row3
        return (Clue(True,  (row1, column1), length),
                Clue(False, (row2, column2), length),
                Clue(True,  (row3, column3), length),
                Clue(False, (row4, column4), length))

    def __init__(self, is_across: bool, start_location: Location, length: int) -> None:
        (row, column) = start_location
        name = f"({row},{column}):{length}:{'A' if is_across else 'D'}"
        self.name = name
        self.is_across = is_across
        self.base_location = start_location
        self.length = length
        slice_start = (row - 1) * 14 + (column - 1)
        if self.is_across:
            self.my_slice = slice(slice_start, slice_start + self.length, 1)
        else:
            self.my_slice = slice(slice_start, slice_start + self.length * 14, 14)

    # @functools.lru_cache(maxsize=None)
    # def to_solver_clue(self) -> SolverClue:
    #     return SolverClue(self.name, self.is_across, self.base_location, self.length)

    def __hash__(self) -> int:
        return self.name.__hash__()

    def __eq__(self, other: 'Clue') -> bool:
        return self.name == other.name

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


class Solver:
    words: Sequence[str]
    unused_quads: Dict[int, int]
    unused_clues: Dict[int, Set[Clue]]
    free_locations: Set[Location]
    results: List[Tuple[str, Clue]]
    allocated_locations_alt: List[int]
    grid: List[str]
    counter: int
    good_counter: int

    def __init__(self, words=WORDS) -> None:
        self.unused_quads = {3: 2, 5: 1, 6: 1, 7: 7, 9: 1}
        words = [word.replace(' ', '') for word in words]

        words.sort(key=lambda word: (self.unused_quads[len(word)], -len(word),
                                        sum(word2.count(ch) ** 2 for ch in word for word2 in words if word != word2)))
        self.words = tuple(words)
        print(words)
        self.unused_clues = {3: set(), 5: set(), 6: set(), 7: set(), 9: set()}
        self.allocated_locations_alt = [0] * 9
        self.results = []
        self.grid = ['.'] * (14 * 14)
        self.counter = self.good_counter = 0

    def run(self, index: int) -> None:
        if index >= len(self.words):
            print(self.results)
            for i in range(0, 196, 14):
                print('  ', ''.join(self.grid[i:i + 14]).upper())
            sys.exit(0)

        word = self.words[index]
        word_length = len(word)

        for clue in list(self.unused_clues[word_length]):
            self.try_word_at_location(index, clue)

        if self.unused_quads[word_length] > 0:
            self.unused_quads[word_length] -= 1
            self.create_new_foursome(index)
            self.unused_quads[word_length] += 1

    def create_new_foursome(self, index) -> None:
        word = self.words[index]
        word_length = len(word)
        for row in range(1, 8):
            saved_allocated_locations = self.allocated_locations_alt[row]
            for column in range(1, 16 - word_length):
                bits = ((1 << word_length) - 1) << column
                if saved_allocated_locations & bits == 0:
                    clues = Clue.get_quad((row, column), word_length)
                    self.allocated_locations_alt[row] |= bits
                    self.unused_clues[word_length].update(clues)
                    for clue in clues[0:2] if index == 0 else clues:
                        self.try_word_at_location(index, clue)
                    self.allocated_locations_alt[row] = saved_allocated_locations
                    self.unused_clues[word_length].difference_update(clues)

    def try_word_at_location(self, index: int, clue: Clue) -> None:
        self.counter += 1
        word = self.words[index]
        grid = self.grid
        my_slice = clue.my_slice
        word_in_grid = grid[my_slice]

        for x, y in zip(word_in_grid, word):
            if x != '.' and x != y:
                return None
        self.good_counter += 1
        self.unused_clues[len(word)].remove(clue)
        self.results.append((word, clue))
        grid[my_slice] = word
        if index < 23:
            print(f'{" | " * index}{word} {clue}')
        self.run(index + 1)
        grid[my_slice] = word_in_grid
        self.results.pop()
        self.unused_clues[len(word)].add(clue)

    # def print_me(self) -> None:
    #     all_clues = []
    #     for _, clue in self.results:
    #         all_clues.append(clue)
    #     for clues in self.unused_clues.values():
    #         all_clues.extend(clues)
    #     solver_clues = [clue.to_solver_clue() for clue in all_clues]
    #     solver_dict = {clue.to_solver_clue(): word for (word, clue) in self.results}
    #
    #     class MySolver (ConstraintSolver):
    #         def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
    #                       location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
    #                       top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:
    #             location_to_clue_number.clear()
    #             super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
    #                               top_bars, left_bars, **more_args)
    #
    #     MySolver(solver_clues).plot_board(solver_dict)



if __name__ == '__main__':
    solver = Solver()
    solver.run(0)
