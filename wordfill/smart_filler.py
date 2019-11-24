import copy
import functools
import importlib
import itertools
import pickle
import sys
from collections import deque
from typing import Sequence, Dict, List, Tuple, Deque, cast, Set, Any, Callable, FrozenSet

Location = Tuple[int, int]

WORDS1 = ("littleowl",
          "elvira",
          "ghost",
          "abs", "ace",
          "abdomen", "brosnan", "courage", "dungeon", "madonna", "neatens", "suntans",)
WORDS2 = ("kit", "wax",
          "entia",
          "undies",
          "anodyne", "interse", "oysters", "poverty", "thyrsus", "wipeout",
          "icedancer",)
WORDS3 = ("edh", "key",
          "adherer", "beastie", "oldhand", "tasered",
          "unshackle",)
WORDS4 = ("rad", "use",
          "thete",
          "athene",
          "appends", "papilla", "resolve", "scalier", "spotter",
         )

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
         "appends", "papilla", "resolve", "scalier", "spotter",
         "little owl",
         )



class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    slice: Any
    locations: Sequence[Location]

    @staticmethod
    @functools.lru_cache(maxsize=None)
    def get_symmetric_clues(start_location: Location, length: int) -> Sequence['Clue']:
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
            self.slice = slice(slice_start, slice_start + self.length, 1)
            self.locations = tuple((row, column + i) for i in range(length))
        else:
            self.slice = slice(slice_start, slice_start + self.length * 14, 14)
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


def verify(func: Callable[['Solver', int, str, int, int], None]) -> Callable[['Solver', int, str, int, int], None]:
    if sys.gettrace() is None:
        return func

    def result(self: 'Solver', index: int, word: str, group: int, word_length: int) -> None:
        saved_available_quads = list(self.available_quads)
        saved_available_queues = [copy.deepcopy(list(queue)) for queue in self.available_clues]
        saved_results = list(self.results)
        saved_allocation_locations = list(self.allocated_locations)
        saved_grid = list(self.grid)
        func(self, index, word, group, word_length)
        assert saved_available_quads == list(self.available_quads)
        assert saved_available_queues == [copy.deepcopy(list(queue)) for queue in self.available_clues]
        assert saved_results == list(self.results)
        assert saved_allocation_locations == list(self.allocated_locations)
        assert saved_grid == list(self.grid)
    return result


AvailableClueItem = Tuple[Clue, List[int]]


class Solver:
    words: Sequence[Tuple[str, int]]
    available_quads: List[int]
    available_clues: Tuple[Deque[AvailableClueItem], ...]
    results: List[Tuple[str, Clue]]
    allocated_locations: List[int]
    grid: List[str]
    counter: int

    INITIAL_AVAILABLE_QUADS = {3: 2, 5: 1, 6: 1, 7: 7, 9: 1}

    def __init__(self) -> None:
        self.available_quads = [Solver.INITIAL_AVAILABLE_QUADS.get(i, 0) for i in range(10)]
        words = ([(word, 1) for word in WORDS1] + [(word, 2) for word in WORDS2] + [(word, 4) for word in WORDS3] +
                 [(word, 8) for word in WORDS4])

        words = [('littleowl', 1),
                 ('icedancer', 2),
                 ('unshackle', 4),
                 ('elvira', 1),
                 ('undies', 2),
                 ('athene', 8),
                 ('ghost', 1),
                 ('entia', 2),
                 ('thete', 8),
                 ('abs', 1),
                 ('ace', 1),
                 ('madonna', 1),
                 ('neatens', 1),
                 ('suntans', 1),
                 ('abdomen', 1),
                 ('brosnan', 1),
                 ('courage', 1),
                 ('dungeon', 1),

                 ('kit', 2),
                 ('wax', 2),
                 ('anodyne', 2),
                 ('interse', 2),
                 ('oysters', 2),
                 ('poverty', 2),
                 ('thyrsus', 2),
                 ('wipeout', 2),
                 ('edh', 4),
                 ('key', 4),
                 ('adherer', 4),
                 ('beastie', 4),
                 ('oldhand', 4),
                 ('tasered', 4),
                 ('rad', 8),
                 ('use', 8),
                 ('appends', 8),
                 ('papilla', 8),
                 ('resolve', 8),
                 ('scalier', 8),
                 ('spotter', 8)]

        print(words)

        self.words = tuple(words)
        self.available_clues = tuple(cast(Deque[AvailableClueItem], deque()) for _ in range(10))
        self.allocated_locations = [0] * 9
        self.results = []
        self.grid = ['.'] * (14 * 14)
        self.counter = 0
        self.test_init()

    def run(self, index: int) -> None:
        if index >= len(self.words):
            print(self.results)
            for i in range(0, 196, 14):
                print('  ', ''.join(self.grid[i:i + 14]).upper())
                self.print_me()
            sys.exit(0)

        # if self.counter >= 1_000_000:
        #     sys.exit(0)
        #
        word, group = self.words[index]
        word_length = len(word)

        available_clues = self.available_clues[word_length]

        if group == 1:
            assert self.available_quads[word_length] > 0
            self.available_quads[word_length] -= 1
            self.find_all_new_quads_and_try_word_at_location(index, word, group, word_length)
            self.available_quads[word_length] += 1
        else:
            assert self.available_quads[word_length] == 0
            for _ in range(len(available_clues)):
                self.try_word_at_location(index, word, group, word_length)
                available_clues.rotate(-1)


    @verify
    def find_all_new_quads_and_try_word_at_location(self, index: int, word: str, group: int, word_length: int) -> None:
        available_clues = self.available_clues[word_length]
        for row in range(1, 8):
            saved_allocated_locations_for_row = self.allocated_locations[row]
            for column in range(1, 16 - word_length):
                bits = ((1 << word_length) - 1) << column
                if saved_allocated_locations_for_row & bits == 0:
                    clues = Clue.get_symmetric_clues((row, column), word_length)
                    self.allocated_locations[row] |= bits
                    temp = [15]
                    for clue in reversed(clues):
                        available_clues.appendleft((clue, temp))
                    if not self.test_grid(index):
                        available_clues.rotate(-4)
                    else:
                        for i in range(4 if index > 0 else 2):
                            self.try_word_at_location(index, word, group, word_length)
                            available_clues.rotate(-1)
                    self.allocated_locations[row] = saved_allocated_locations_for_row
                    for _ in range(4):
                        available_clues.pop()

    MAX_SHOW = 12

    @verify
    def try_word_at_location(self, index: int, word: str, group: int, word_length: int) -> None:
        self.counter += 1
        available_clues = self.available_clues[word_length]
        this_available_clue = available_clues[0]
        this_clue, this_array = this_available_clue

        if not(this_array[0] & group):
            return None

        grid = self.grid
        clue_slice = this_clue.slice
        word_in_grid = grid[clue_slice]


        for x, y in zip(word_in_grid, word):
            if x != '.' and x != y:
                return None

        available_clues.popleft()
        self.results.append((word, this_clue))
        grid[clue_slice] = word
        if not self.test_grid(index + 1):
            pass
        else:
            if index < self.MAX_SHOW:
                print(f'{" | " * index}{word} {this_clue} {self.counter:,} =>')
            this_array[0] -= group #  We already know the bit is set
            self.run(index + 1)
            this_array[0] += group
        grid[clue_slice] = word_in_grid
        self.results.pop()
        available_clues.appendleft(this_available_clue)

    suffixes: Sequence[Sequence[str]]
    first_letters: Sequence[FrozenSet[str]]
    big_word_set: FrozenSet[str]
    little_word_set: Tuple[FrozenSet[str], ...]

    def test_init(self) -> None:
        words = [word for word, _ in self.words]
        self.suffixes = tuple((tuple(x for x in words[i:] if len(x) == 7) if len(word) == 7 else ())
                              for i, word in enumerate(words))
        self.first_letters = tuple(frozenset(word[0] for word in words) for words in self.suffixes)

        self.little_word_set = tuple(frozenset(pattern for word in words for pattern in self.__all_forms_of_word(word))
                                 for words in self.suffixes)
        with open("wordlist/biglist.pcl", "rb") as file:
            self.big_word_set = frozenset(pickle.load(file))


    DEAD_SET = set('.abcdefghijkl' 'opqrst')

    def test_grid(self, index: int):
        grid = self.grid

        live_set = self.first_letters[index]

        available_clues = self.available_clues[7]
        for clue, _ in available_clues:
            start_ch = grid[clue.slice.start]
            is_okay = start_ch in Solver.DEAD_SET or start_ch in live_set
            if not is_okay:
                return False

        for clue, _ in self.available_clues[6]:
            start_ch = grid[clue.slice.start]
            if start_ch not in '.defg':
                return False

        seen_bad = 0
        really_bad = 0
        for clue, _ in available_clues:
            word_in_grid = ''.join(grid[clue.slice])
            if word_in_grid in self.little_word_set[index]:
                continue
            seen_bad += 1
            if seen_bad > 6:
                return False
            if word_in_grid not in self.big_word_set:
                really_bad += 1
                if really_bad >= 2:
                    return False

        return True

    @staticmethod
    def get_big_word_list() -> Sequence[str]:
        result: Set[str] = set()
        def get_word(n: int):
            with open(f"wordlist/{n}", "r") as f:
                words = f.readlines()
            words = [x.strip() for x in words]
            return words
        five = get_word(5)
        six = get_word(6)
        seven = get_word(7)
        result.update(seven)
        result.update([x + 's' for x in six])
        result.update([x + 'd' for x in six if x[-1] == 'e'])
        result.update([x + 'ed' for x in five])
        result.update([x[:4] + 'ies' for x in five if x[-1] == 'y'])
        result.update([x[:4] + 'ied' for x in five if x[-1] == 'y'])
        def foobar(word, index):
            return ''.join(word[i] if index & (1 << i) else '.' for i in range(7))
        temp = [foobar(word, index) for word in result for index in range(1 << 7)]
        temp = set(temp)
        print(len(temp))
        return tuple(sorted(result))

    def print_me(self) -> None:
        module = importlib.import_module("solver")
        all_clues = []
        for _, clue in self.results:
            all_clues.append(clue)
        for available_clue_list in self.available_clues:
            for clue, _ in available_clue_list:
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

    @staticmethod
    def __all_forms_of_word(word: str) -> Sequence[str]:
            pairs = [('.', ch) for ch in word]
            result = [''.join(letters) for letters in itertools.product(*pairs)]
            return result


if __name__ == '__main__':
    solver = Solver()
    solver.run(0)
