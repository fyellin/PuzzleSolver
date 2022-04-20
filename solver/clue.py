from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Callable, FrozenSet, Iterable, Optional, Sequence, Union

from .clue_types import Location
from .evaluator import Evaluator

ClueValueGenerator = Callable[['Clue'], Iterable[Union[str, int]]]


class Clue:
    name: str
    is_across: bool
    base_location: Location
    length: int
    evaluators: Sequence[Evaluator]
    generator: Optional[ClueValueGenerator]
    context: Any
    locations: Sequence[Location]
    location_set:  FrozenSet[Location]
    expression: str

    def __init__(self, name: str, is_across: bool, base_location: Location, length: int, *,
                 expression: str = '',
                 generator: Optional[ClueValueGenerator] = None,
                 context: Any = None,
                 locations: Optional[Iterable[Location]] = None):
        self.name = name
        self.is_across = is_across
        if locations:
            self.locations = tuple(locations)
            self.base_location = self.locations[0]
            self.length = len(self.locations)
        else:
            self.base_location = (row, column) = base_location
            self.length = length
            if self.is_across:
                self.locations = tuple((row, column + i) for i in range(length))
            else:
                self.locations = tuple((row + i, column) for i in range(length))
        if expression:
            assert not expression.startswith('@')
            self.evaluators = self.create_evaluators(expression)
        else:
            self.evaluators = ()
        self.expression = expression or ''
        self.generator = generator
        self.context = context
        self.location_set = frozenset(self.locations)

    def location(self, i: int) -> Location:
        return self.locations[i]

    @classmethod
    def create_evaluators(cls, expression: str,
                          mapping: Optional[Mapping[str, Callable]] = None
                          ) -> Sequence[Evaluator]:
        if mapping is None:
            mapping = {}
        return Evaluator.from_string(expression, mapping)

    @classmethod
    def create_callable(cls, expression: str,
                        mapping: Optional[Mapping[str, Callable]] = None) -> Callable:
        assert '=' not in expression
        evaluator, = cls.create_evaluators(expression, mapping)
        return evaluator.callable

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)
