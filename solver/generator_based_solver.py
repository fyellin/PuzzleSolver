from __future__ import annotations

import re
from abc import abstractmethod
from collections import defaultdict
from collections.abc import Callable, Sequence
from typing import Any

from .base_solver import BaseSolver, KnownClueDict
from .clue import Clue
from .clue_types import ClueValue


class GeneratorBasedSolver(BaseSolver):
    """Intermediate base for solvers that fill clues from per-clue generators.

    Provides shared machinery for candidate generation, singleton and multi-clue
    constraints, and the check_solution / show_solution override hooks.
    Concrete subclasses must implement _add_multi_constraint and solve.
    """

    _singleton_constraints: dict[Clue, list[Callable[..., bool]]]

    def __init__(self, clue_list: Sequence[Clue], **kwargs: Any) -> None:
        super().__init__(clue_list, **kwargs)
        self._singleton_constraints = defaultdict(list)

    def add_constraint(self, clues: Sequence[Clue | str] | str,
                       predicate: Callable[*tuple[ClueValue, ...], bool],
                       *, name: str | None = None) -> None:
        """Register an additional constraint.

        Single-clue predicates pre-filter candidates before solving starts.
        Multi-clue predicates are forwarded to _add_multi_constraint for
        solver-specific handling.
        """
        if isinstance(clues, str):
            clues = clues.split()
        actual_clues = tuple(
            c if isinstance(c, Clue) else self.clue_named(c) for c in clues
        )
        actual_name = name or '-'.join(c.name for c in actual_clues)
        if len(actual_clues) == 1:
            self._singleton_constraints[actual_clues[0]].append(predicate)
        else:
            self._add_multi_constraint(actual_clues, predicate, actual_name)

    @abstractmethod
    def _add_multi_constraint(self, clues: tuple[Clue, ...],
                              predicate: Callable[*tuple[ClueValue, ...], bool],
                              name: str) -> None:
        """Register a multi-clue constraint; implementation is solver-specific."""

    def get_initial_values_for_clue(self, clue: Clue) -> list[ClueValue]:
        """Generate all valid candidates for a clue.

        Filters by the no-leading-zero pattern derived from clue locations, then
        by any registered singleton constraints.
        """
        pattern = re.compile(
            ''.join(self.get_allowed_regexp(loc) for loc in clue.locations)
        )
        predicates = self._singleton_constraints[clue]
        result = []
        for x in clue.generator(clue):
            v = str(x) if isinstance(x, int) else x
            if pattern.fullmatch(str(v)) and all(p(v) for p in predicates):
                result.append(v)
        return sorted(result)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        """Override to add final solution validation."""
        return True

    def show_solution(self, known_clues: KnownClueDict) -> None:
        """Override for custom display; default plots the board."""
        self.plot_board(known_clues)
