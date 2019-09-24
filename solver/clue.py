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
    location_list: Sequence[Location]
    location_set:  FrozenSet[Location]

    def __init__(self, name: str, is_across: bool, base_location: Location, length: int, *,
                 expression: str = '',
                 generator: Optional[ClueValueGenerator] = None,
                 context: Any = None):
        self.name = name
        self.is_across = is_across
        self.base_location = base_location
        self.length = length
        if expression:
            python_pieces = Clue.convert_expression_to_python(expression)
            self.evaluators = tuple(map(Evaluator.make, python_pieces))
        else:
            self.evaluators = ()
        self.generator = generator
        self.context = context
        self.location_list = tuple(self.generate_location_list())
        self.location_set = frozenset(self.location_list)

    def generate_location_list(self) -> Iterable[Location]:
        row, column = self.base_location
        column_delta, row_delta = (1, 0) if self.is_across else (0, 1)
        for i in range(self.length):
            yield row + i * row_delta, column + i * column_delta

    def locations(self) -> Sequence[Location]:
        return self.location_list

    def location(self, i: int) -> Location:
        return self.location_list[i]

    @staticmethod
    def convert_expression_to_python(expression: str) -> Sequence[str]:
        expression = expression.replace("–", "-")   # Magpie use a strange minus sign
        expression = expression.replace('−', '-')   # Listener uses a different strange minus sign
        expression = expression.replace("^", "**")  # Replace exponentiation with proper one
        for _ in range(2):
            # ), letter, or digit followed by (, letter, or digit needs an * in between, except when we have
            # two digits in a row with no space between them.  Note negative lookahead below.
            expression = re.sub(r'(?!\d\d)([\w)])\s*([(\w])', r'\1*\2', expression)
        return expression.split('=')

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Any) -> bool:
        return self is other

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)
