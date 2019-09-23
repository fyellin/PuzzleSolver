from abc import ABC, abstractmethod

from ClueList import ClueList


class BaseSolver(ABC):
    clue_list: ClueList
    allow_duplicates: bool

    def __init__(self, clue_list: ClueList, *, allow_duplicates: bool = False) -> None:
        self.clue_list = clue_list
        self.allow_duplicates = allow_duplicates

    @abstractmethod
    def solve(self, *, show_time: bool = True, debug: bool = False) -> int: ...
