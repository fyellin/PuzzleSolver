import functools
import importlib
import itertools
import os
import pickle
import re
import sys
from collections import deque
from typing import Sequence, Dict, List, Tuple, Deque, cast, Set, Any, Callable

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
         "appends", "papilla", "resolve", "scalier", "spotter",
         "little owl",
         )


class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    slice: slice
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

    def __eq__(self, other: 'Clue') -> bool:
        return self.name == other.name

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)


def verify(func: Callable[['Solver', int, str, int], None]) -> Callable[['Solver', int, str, int], None]:
    if sys.gettrace() is None:
        return func

    def result(self: 'Solver', index: int, word: str, word_length: int) -> None:
        temp1 = list(self.available_quads)
        temp2 = [list(queue) for queue in self.available_clues]
        temp3 = list(self.results)
        temp4 = list(self.allocated_locations)
        temp5 = list(self.grid)
        func(self, index, word, word_length)
        assert temp1 == list(self.available_quads)
        assert temp2 == [list(queue) for queue in self.available_clues]
        assert temp3 == list(self.results)
        assert temp4 == list(self.allocated_locations)
        assert temp5 == list(self.grid)
    return result


class Solver:
    words: Sequence[str]
    available_quads: List[int]
    available_clues: Tuple[Deque[Clue]]
    results: List[Tuple[str, Clue]]
    allocated_locations: List[int]
    grid: List[str]
    counter: int

    INITIAL_AVAILABLE_QUADS = {3: 2, 5: 1, 6: 1, 7: 7, 9: 1}

    def __init__(self, words=WORDS) -> None:
        self.available_quads = [Solver.INITIAL_AVAILABLE_QUADS.get(i, 0) for i in range(10)]
        words = [word.replace(' ', '') for word in words]
        words.sort(key=lambda word: (self.available_quads[len(word)], -len(word),
                                     (0 if re.search(r'[qvxyz]', word) else
                                      1 if word[0] in 'nm' else
                                      2 if re.search('r[mn]', word) else
                                      3),
                                     sum(word2.count(ch) ** 2 for ch in word for word2 in words if word != word2)))
        self.words = tuple(words)
        print(words)
        self.available_clues = tuple(cast(Deque[Clue], deque()) for _ in range(10))
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

        if self.counter >= 1_000_000:
            sys.exit(0)

        word = self.words[index]
        word_length = len(word)

        available_clues = self.available_clues[word_length]

        for _ in range(len(available_clues)):
            self.try_word_at_location(index, word, word_length)
            available_clues.rotate(-1)

        if self.available_quads[word_length] > 0:
            self.available_quads[word_length] -= 1
            self.find_all_new_quads_and_try_word_at_location(index, word, word_length)
            self.available_quads[word_length] += 1

    @verify
    def find_all_new_quads_and_try_word_at_location(self, index: int, word: str, word_length: int) -> None:
        available_clues = self.available_clues[word_length]
        for row in range(1, 8):
            saved_allocated_locations_for_row = self.allocated_locations[row]
            for column in range(1, 16 - word_length):
                bits = ((1 << word_length) - 1) << column
                if saved_allocated_locations_for_row & bits == 0:
                    clues = Clue.get_symmetric_clues((row, column), word_length)
                    self.allocated_locations[row] |= bits
                    available_clues.extendleft(reversed(clues))
                    if word_length == 7 and not self.quick_sanity_test(available_clues, index):
                        available_clues.rotate(-4)
                    else:
                        for i in range(4 if index > 0 else 2):
                            self.try_word_at_location(index, word, word_length)
                            available_clues.rotate(-1)
                    self.allocated_locations[row] = saved_allocated_locations_for_row
                    for _ in range(4):
                        available_clues.pop()

    @verify
    def try_word_at_location(self, index: int, word: str, word_length: int) -> None:
        self.counter += 1
        available_clues = self.available_clues[word_length]
        this_clue = available_clues[0]
        grid = self.grid
        clue_slice = this_clue.slice
        word_in_grid = grid[clue_slice]

        for x, y in zip(word_in_grid, word):
            if x != '.' and x != y:
                return None

        available_clues.popleft()
        self.results.append((word, this_clue))
        grid[clue_slice] = word
        if word_length == 7 and not self.quick_sanity_test(available_clues, index + 1):
            pass
        else:
            if index < 12:
                print(f'{" | " * index}{word} {this_clue} {self.counter}')
            self.run(index + 1)
        grid[clue_slice] = word_in_grid
        self.results.pop()
        available_clues.appendleft(this_clue)

    suffixes: Sequence[Sequence[str]]
    first_letters: Sequence[Set[str]]
    big_word_set: Set[str]

    def test_init(self) -> None:
        words = self.words
        self.suffixes = tuple((() if len(word) != 7 else tuple(words[i:])) for i, word in enumerate(words))
        self.first_letters = tuple(set(word[0] for word in words) for words in self.suffixes)
        print(os.getcwd())
        print(os.listdir('.'))
        with open("../wordfill/wordlist/biglist.pcl", "rb") as file:
            self.big_word_set = pickle.load(file)



    DEAD_SET = set('.abcdefghijkl' 'opqrst')

    def quick_sanity_test(self, available_clues: Sequence[Clue], index: int) -> None:
        grid = self.grid

        def match(clue: Clue) -> bool:
            match_words = self.suffixes[index]
            word_in_grid = grid[clue.slice]
            for i, ch in enumerate(word_in_grid):
                if ch != '.':
                    match_words = [word for word in match_words if word[i] == ch]
                    if not match_words:
                        return False
            return bool(match_words)

        def bigmatch(clue: Clue) -> bool:
            word_in_grid = ''.join(grid[clue.slice])
            return word_in_grid in self.big_word_set

        live_set = self.first_letters[index]

        for clue in available_clues:
            start_ch = grid[clue.slice.start]
            is_okay = start_ch in Solver.DEAD_SET or start_ch in live_set
            if not is_okay:
                return False

        for clue in self.available_clues[6]:
            start_ch = grid[clue.slice.start]
            if start_ch not in '.defg':
                return False

        if len(available_clues) <= 6:
            return True

        seen_bad = 0
        really_bad = 0
        unknown = len(available_clues)
        for clue in available_clues:
            unknown -= 1
            if match(clue):
                if seen_bad + unknown <= 6:
                    break
            else:
                seen_bad += 1
                if seen_bad > 6:
                    return False
                if not bigmatch(clue):
                    really_bad += 1
                    if really_bad >= 2:
                        return False

        return True

    @staticmethod
    def get_big_word_list() -> Sequence[str]:
        result = set()
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
        for clues in self.available_clues:
            all_clues.extend(clues)
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
