# -*- coding: utf-8 -*-

import collections
import copy
import sys
from operator import itemgetter
from typing import Optional, Callable, Sequence, Dict, Any, TextIO, Set, Iterator, List, Hashable, \
    TypeVar, NamedTuple, Generic, Mapping

ConstraintName = TypeVar('ConstraintName', bound=Hashable)
Constraint = TypeVar('Constraint', bound=Hashable)


class DancingLinks(Generic[ConstraintName, Constraint]):
    constraints: Mapping[ConstraintName, Sequence[Constraint]]
    optional_constraints: Set[Constraint]
    row_printer: Any

    count: int
    max_depth: int
    output: TextIO
    debug: int
    X: Dict[Constraint, Set[ConstraintName]]

    def __init__(self, constraints: Mapping[ConstraintName, Sequence[Constraint]],
                 *, row_printer: Optional[Callable[[Sequence[ConstraintName]], None]] = None,
                 optional_constraints: Optional[Set[Constraint]] = None):
        """The entry to the Dancing Links code.  Y should be a dictionary.  Each key
        is the name of the row (something meaningful to the user).  The value should
        be a list/tuple of the constraints satisfied by this row.

        The row names and constraint names s can be anything immutable and hashable.
        Typically they are strings, but feel free to use whatever works best.
        """
        self.constraints = constraints
        self.optional_constraints = optional_constraints or set()
        self.row_printer = row_printer or (lambda solution: print(sorted(solution)))
        if optional_constraints:
            constraints = dict(self.constraints)
            for constraint in optional_constraints:
                constraints[OptionalConstraint(constraint)] = [constraint]
            self.constraints = constraints

    def solve(self, output: TextIO = sys.stdout, debug: Optional[int] = None) -> None:
        # Create the cross reference giving the rows in which each constraint appears
        reverse_constraints: Dict[Constraint, Set[ConstraintName]] = collections.defaultdict(set)
        for constraint_name, constraints in self.constraints.items():
            for constraint in constraints:
                reverse_constraints[constraint].add(constraint_name)
        runner = copy.copy(self)

        runner.X = reverse_constraints
        runner.output = output
        runner.count = 0
        runner.debug = debug is not None
        runner.max_depth = debug if debug is not None else -1

        if runner.debug:
            output.write(f"There are {len(runner.constraints)} rows and {len(reverse_constraints)} constraints\n")
        solutions = 0
        for solution in runner._solve_constraints(0):
            solutions += 1
            self.row_printer(solution)
        if runner.debug:
            print("Count =", runner.count, file=output)
            print("Solutions =", solutions, file=output)

    def _solve_constraints(self, depth: int) -> Iterator[List[ConstraintName]]:
        """Returns a set of rows that satisfies the constraints of X
        """
        # Note that "depth" is meaningful only when debugging.
        self.count += 1
        is_debugging = depth < self.max_depth

        constraints_and_length = [(len(value), name) for name, value in self.X.items()]

        if not constraints_and_length:
            if is_debugging:
                self.output.write(f"{self._indent(depth)}✓ SOLUTION\n")
            yield []
            return

        current_count = 0
        old_depth = depth

        min_count, min_constraint = min(constraints_and_length, key=itemgetter(0))
        depth += (min_count != 1)
        if min_count == 0:
            if is_debugging:
                self.output.write(f"{self._indent(depth)}✕ {min_constraint}\n")
            return

        # Look at each possible row that can resolve the min_constraint.
        min_constraint_rows = self._cover_constraint(min_constraint)

        for row in min_constraint_rows:
            cols = [self._cover_constraint(row_constraint)
                    for row_constraint in self.constraints[row] if row_constraint != min_constraint]

            if is_debugging:
                indent = self._indent(old_depth)
                live_constraint_names = {name for names in self.X.values() for name in names}
                current_count += 1
                if min_count == 1:
                    if not isinstance(row, OptionalConstraint):
                        self.output.write(f"{indent}• {min_constraint}: "
                                          f"Row {row} ({len(live_constraint_names)} rows)\n")
                else:
                    self.output.write(f"{indent}{current_count}/{min_count} {min_constraint}: "
                                      f"Row {row} ({len(live_constraint_names)} rows)\n")

            for s in self._solve_constraints(depth):
                if not isinstance(row, OptionalConstraint):
                    s.append(row)
                yield s

            for row_constraint in reversed(self.constraints[row]):
                if row_constraint != min_constraint:
                    self._uncover_constraint(row_constraint, cols.pop())

        self._uncover_constraint(min_constraint, min_constraint_rows)

    def _cover_constraint(self, constraint: Constraint) -> Set[ConstraintName]:
        rows = self.X.pop(constraint)
        for row in rows:
            # For each constraint in this row about to be deleted
            for row_constraint in self.constraints[row]:
                # Mark this feature as now longer available in the row,
                # unless we're looking at the feature we just chose!
                if row_constraint != constraint:
                    self.X[row_constraint].remove(row)
        return rows

    def _uncover_constraint(self, constraint: Constraint, rows: Set[ConstraintName]) -> None:
        for row in rows:
            for row_constraint in self.constraints[row]:
                if row_constraint != constraint:
                    self.X[row_constraint].add(row)
        self.X[constraint] = rows

    @staticmethod
    def _indent(depth: int) -> str:
        return ' | ' * depth


class OptionalConstraint(NamedTuple, Generic[Constraint]):
    constraint: Constraint

    def __str__(self) -> str:
        return f"<? {self.constraint}>"
