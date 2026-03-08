from collections.abc import Callable, Iterable, Sequence

from .clue_types import ClueValue, Location
from .evaluator import Evaluator

ClueValueGenerator = Callable[['Clue'], Iterable[str | int | ClueValue]]


class Clue[T]:
    name: str
    is_across: bool
    base_location: Location
    length: int
    evaluators: Sequence[Evaluator]
    generator: ClueValueGenerator | None
    context: T
    locations: Sequence[Location]
    location_set:  frozenset[Location]
    expression: str
    priority: int  # When ordering in the evaluation solver

    def __init__(self, name: str, is_across: bool, base_location: Location, length: int, *,
                 expression: str = '',
                 generator: ClueValueGenerator | None = None,
                 context: T = None,
                 locations: Iterable[Location] | None = None,
                 priority=0):
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
            self.evaluators = Evaluator.create_evaluators(expression)
        else:
            self.evaluators = ()
        self.expression = expression or ''
        self.generator = generator
        self.context = context
        self.location_set = frozenset(self.locations)
        self.priority = priority

    def location(self, i: int) -> Location:
        return self.locations[i]

    def dancing_links_rc_constraints(
            self, value: ClueValue | int | str) -> Sequence[tuple[str, str]]:
        """
        Provides a map from the encoding location to its current value. The key is
        either the tuple (r, c) or the string "r{row}c{column}" depending on the value
        of dancing_links.
        """
        return [
            (f'r{r}c{c}', ch)
            for ch, (r, c) in zip(str(value), self.locations, strict=True)
        ]

    __hash__ = object.__hash__

    __eq__ = object.__eq__

    def __str__(self) -> str:
        return f'<Clue {self.name}>'

    def __repr__(self) -> str:
        return str(self)

    # The following let us pickle and unpickle clues. We need to set a global indicating
    # the solver that was used for creating the clues by calling set_pickle solver.

    def __reduce__(self):
        return Clue._pickle_get_named, (self.name,)

    @staticmethod
    def set_pickle_solver(solver):
        Clue._pickle_solver = solver

    @staticmethod
    def _pickle_get_named(name: str):
        return Clue._pickle_solver.clue_named(name)
