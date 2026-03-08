from __future__ import annotations

from collections.abc import Callable, Hashable, Sequence
from typing import Any

from .base_solver import KnownClueDict
from .clue import Clue
from .clue_types import ClueValue
from .dancing_links import DancingLinks, DancingLinksBounds, DLConstraint
from .generator_based_solver import GeneratorBasedSolver


class DancingLinksSolver(GeneratorBasedSolver):
    """Solves grid-fill puzzles via Algorithm X (Dancing Links with colors).

    Each Clue must have a generator that yields candidate values.  Intersection
    constraints are encoded as secondary (colored) columns, so Algorithm X
    enforces digit consistency at crossing squares automatically — no explicit
    intersection propagation is needed.

    When allow_duplicates=False (the default), uniqueness is also enforced via
    colored secondary columns: two clues sharing the same value would color the
    same column with different colors, which Algorithm X treats as a conflict.

    Override update_constraints() to inject additional rows or columns into the
    DL matrix before solving.  Solution rows with non-Clue keys are ignored when
    assembling the KnownClueDict passed to check_solution/show_solution.
    """

    _multi_constraints: list[tuple[tuple[Clue, ...], Callable[..., bool]]]
    _solution_count: int

    def __init__(self, clue_list: Sequence[Clue], **kwargs: Any) -> None:
        super().__init__(clue_list, **kwargs)
        self._multi_constraints = []

    def _add_multi_constraint(self, clues: tuple[Clue, ...],
                              predicate: Callable[..., bool],
                              name: str) -> None:
        self._multi_constraints.append((clues, predicate))

    def update_constraints(self, constraints: dict[Hashable, list[DLConstraint]],
                           optional_constraints: set[str],
                           bounds: dict[str, tuple[int, int]]) -> None:
        """Override to add or modify the DL matrix before solving.

        Add new rows to constraints with any hashable key; declare new secondary
        column names in optional_constraints.  Rows whose key is not a
        (Clue, ClueValue) tuple are ignored when assembling the solution dict.
        Populate bounds to use DancingLinksBounds instead of DancingLinks.
        """

    def solve(self, *, show_time: bool = True, debug: bool = False,
              max_debug_depth: int | None = None) -> int:
        self._solution_count = 0

        # Secondary column per grid cell, colored with the digit placed there —
        # the color mechanism makes Algorithm X enforce intersection consistency.
        optional_constraints: set[str] = {
            f"r{row}c{col}" for clue in self._clue_list for row, col in clue.locations
        }

        constraints: dict[Hashable, list[DLConstraint]] = {}
        for clue in self._clue_list:
            if not clue.generator:
                continue
            for value in self.get_initial_values_for_clue(clue):
                row_items: list[DLConstraint] = [
                    f"clue_{clue.name}",
                    *self.get_clue_rc_constraints(clue, value),
                    *self.get_clue_value_constraints(clue, value, optional_constraints)
                ]
                constraints[clue, value] = row_items

        bounds: dict = {}
        self.update_constraints(constraints, optional_constraints, bounds)

        def on_solution(rows: Sequence[Hashable]) -> None:
            if not self.check_raw_solution(rows):
                return
            known_clues: KnownClueDict = {
                row[0]: row[1] for row in rows
                if isinstance(row, tuple) and len(row) == 2 and isinstance(row[0], Clue)
            }
            for clues, predicate in self._multi_constraints:
                if not predicate(*(known_clues[c] for c in clues)):
                    return
            if not self.check_solution(known_clues):
                return
            self._solution_count += 1
            self.show_solution(known_clues)

        if bounds:
            dl = DancingLinksBounds(constraints, row_printer=on_solution,
                                    optional_constraints=optional_constraints,
                                    bounds=bounds)
        else:
            dl = DancingLinks(constraints, row_printer=on_solution,
                              optional_constraints=optional_constraints)
        dl.solve(debug=debug, max_debug_depth=max_debug_depth)
        return self._solution_count

    def get_clue_rc_constraints(self, clue: Clue, value: ClueValue) -> Sequence[DLConstraint]:
        """Return the row/column constraints for a clue/value pair.

        Override to substitute different or additional rc constraints.
        """
        return clue.dancing_links_rc_constraints(value)

    def get_clue_value_constraints(
            self, clue, value: ClueValue, optional_constraints) -> Sequence[DLConstraint]:
        if not self._allow_duplicates and len(value) > 1:
            optional_constraints.add(f"val_{value}")
            return [(f"val_{value}", clue.name)]
        else:
            return []

    def check_raw_solution(self, rows: Sequence[Hashable]) -> bool:
        return True
