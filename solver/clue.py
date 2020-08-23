from __future__ import annotations

import re
from typing import Iterable, Optional, Any, FrozenSet, Sequence, Callable, Union

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
            if not expression.startswith('@'):
                python_pieces = Clue.__convert_expression_to_python(expression)
            else:
                python_pieces = expression[1:],
            self.evaluators = tuple(Evaluator.make(piece) for piece in python_pieces)
        else:
            self.evaluators = ()
        self.expression = expression or ''
        self.generator = generator
        self.context = context
        self.location_set = frozenset(self.locations)

    def location(self, i: int) -> Location:
        return self.locations[i]

    @staticmethod
    def __convert_expression_to_python(expression: str) -> Sequence[str]:
        expression = expression.replace("–", "-")   # magpie use a strange minus sign
        expression = expression.replace('−', '-')   # Listener uses a different strange minus sign
        expression = expression.replace("^", "**")  # Replace exponentiation with proper one
        for _ in range(2):
            # ), letter, or digit followed by (, letter, or digit needs an * in between, except when we have
            # two digits in a row with no space between them.  Note negative lookahead below.
            expression = re.sub(r'(?!\d\d)([\w)])\s*([(\w])', r'\1*\2', expression)
        if '!' in expression:
            expression = re.sub(r'(\w)!', r'math.factorial(\1)', expression)
        return expression.split('=')

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)
