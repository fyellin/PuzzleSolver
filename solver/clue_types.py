from abc import ABC, abstractmethod
from typing import Protocol

type Location = tuple[int, int]
type Letter = str


class ClueValue(Protocol):
    def __str__(self) -> str: ...
    def __int__(self) -> int: ...
    def __len__(self) -> int: ...
    def __getitem__(self, key: int | slice) -> str: ...


class AbstractClueValue(ClueValue, ABC):
    """
    Base implementation for clue values whose grid text is a single string.
    It uses a passed in string for __len__, __getitem__, and __str__
    """

    __slots__ = ('_text',)

    def __init__(self, text: str) -> None:
        self._text = text

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    @abstractmethod
    def __hash__(self) -> int: ...

    @abstractmethod
    def __lt__(self, other: object) -> bool: ...

    def __str__(self) -> str:
        return self._text

    def __int__(self) -> int:
        return int(self._text)

    def __len__(self) -> int:
        return len(self._text)

    def __getitem__(self, key: int | slice) -> str:
        return self._text[key]
