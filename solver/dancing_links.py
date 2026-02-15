from __future__ import annotations

import bisect
from itertools import chain, count
from collections import Counter
from collections.abc import Hashable, Sequence
from datetime import datetime
from functools import cache
from typing import Any, Callable, Final, Optional

import math


class _Purified:
    __slots__ = ()


PURIFIED: Final = _Purified()

type DLConstraint = str | tuple[str, str]


class DancingLinks[Row: Hashable]:
    constraints: dict[Row, list[DLConstraint]]
    optional_constraints: set[str]
    row_printer: Optional[Callable[[Sequence[Row]], None]]
    names: dict[int, str]
    spacer_indices: list[int]
    memory: list[list[Optional[int]]]
    colors: dict[int, str | _Purified]
    debug: bool
    max_debugging_depth: int

    def __init__(
        self,
        constraints: dict[Row, list[DLConstraint]],
        *,
        row_printer: Optional[Callable[[Sequence[Row]], None]] = None,
        optional_constraints: Optional[set[str]] = None,
    ):
        """The entry to the Dancing Links code.  constraints should be a dictionary.
        Each key is the name of the row (something meaningful to the user).
        The value should be a list/tuple of the row_to_constraints satisfied by this row.

        The row names and constraint names can be anything immutable and hashable.
        Typically, they are strings, but feel free to use whatever works best. Also,
        all constraint names must be "comparable" to each other. So strings really do work
        best
        """
        self.constraints = constraints
        self.optional_constraints = optional_constraints or set()
        self.row_printer = row_printer or self._default_row_printer

    def solve(self, debug: Optional[int] = 0) -> None:
        time1 = datetime.now()
        self.debug = debug is not None
        self.max_debugging_depth = debug if debug is not None else -1

        (*self.memory, self.colors, self.names, self.spacer_indices) = (
            self.create_data_structure()
        )
        steps, solutions = self.inner_solve()

        time2 = datetime.now()
        print("Steps =", steps)
        print("Solutions =", solutions)
        print("Time =", (time2 - time1))

    def inner_solve(self) -> tuple[int, int]:
        down: list[int]
        left, right, lengths, up, down, top = self.memory
        colors = self.colors
        visible_rows = len(self.spacer_indices)

        def search_iterative() -> tuple[int, int]:
            steps = solutions = 0
            stack: list[list[int]] = [[0, 0, 0, 0]]

            while stack:
                depth, r, min_constraint, index = frame = stack.pop()
                if r > 0:
                    # r is the row before the one I want to scan.  If r == min_constraint,
                    # then this is the first row, and I don't have a row to uncover
                    if r != min_constraint:
                        uncover_row(r)

                    r = down[r]
                    # The next time we reach min_constraint, the column is exhausted.
                    if r == min_constraint:
                        uncover_item(min_constraint)
                        continue

                    cover_row(r)

                    frame[1], frame[3] = r, index + 1  # reuse previous frame.
                    stack.append(frame)
                    if self.debug <= self.max_debugging_depth:
                        self.__print_debug_info(
                            depth,
                            min_constraint,
                            self.get_name(r),
                            index,
                            lengths[min_constraint],
                            visible_rows,
                        )
                        depth += lengths[min_constraint] != 1

                    # stack.append((depth, 0, 0, 0))
                    # Fall through

                steps += 1
                if right[0] == 0:
                    if self.debug <= self.max_debugging_depth:
                        print(f"{self.__indent(depth)}✓ SOLUTION")
                    # There can't be any frames with r == 0.
                    solution = [s[1] for s in stack if s[1] != s[2]]
                    solutions += 1
                    self.row_printer([self.get_name(r) for r in solution])
                    continue

                min_constraint, min_count = choose_column()

                if min_count == 0:
                    if self.debug <= self.max_debugging_depth:
                        print(f"{self.__indent(depth)}✕ {self.names[min_constraint]}")
                    continue

                cover_item(min_constraint)
                stack.append([depth, min_constraint, min_constraint, 1])
            return steps, solutions

        def cover_row(r: int) -> None:
            """Called when we're adding row r to the solution set"""
            j = r + 1
            while j != r:
                tt = top[j]
                if tt <= 0:
                    # This is a spacer, and spacers form a proper vertical chain
                    j = up[j]
                else:
                    commit_item(j, tt)
                j += 1

        def uncover_row(r: int) -> None:
            """Called when we're removing row r from the solution set"""
            j = r - 1
            while j != r:
                tt = top[j]
                if tt <= 0:
                    # This is a spacer, and spacers form a proper vertical chain.
                    j = down[j]
                else:
                    uncommit_item(j, tt)
                j -= 1

        def cover_item(item: int) -> None:  # Remove the item i
            ll, rr = left[item], right[item]
            left[rr], right[ll] = ll, rr
            row = down[item]
            while row != item:
                hide(row)
                row = down[row]

        def uncover_item(item) -> None:
            row = up[item]
            while row != item:
                unhide(row)
                row = up[row]
            ll, rr = left[item], right[item]
            right[ll] = left[rr] = item

        def hide(row: int) -> None:
            nonlocal visible_rows
            visible_rows -= 1
            j = row + 1
            while j != row:
                tt, uu, dd = top[j], up[j], down[j]
                if tt <= 0:
                    j = uu  # goto previous spacer
                elif colors.get(j) is not PURIFIED:
                    up[dd], down[uu] = uu, dd
                    lengths[tt] -= 1
                j += 1

        def unhide(row: int) -> None:
            nonlocal visible_rows
            visible_rows += 1
            j = row - 1
            while j != row:
                tt, uu, dd = top[j], up[j], down[j]
                if tt <= 0:
                    j = dd
                elif colors.get(j) is not PURIFIED:
                    lengths[tt] += 1
                    down[uu] = up[dd] = j
                j -= 1

        def commit_item(item: int, item_top: int) -> None:
            assert item_top == top[item]
            color = colors.get(item)
            if color is None:
                cover_item(item_top)
            elif color is not PURIFIED:
                purify(item, color, item_top)

        def uncommit_item(item: int, item_top: int) -> None:
            assert item_top == top[item]
            color = colors.get(item)
            if color is None:
                uncover_item(item_top)
            elif color is not PURIFIED:
                unpurify(item, color, item_top)

        def purify(p: int, color: str, top: int) -> None:
            assert color == colors[p] and color is not None
            q = down[top]
            while q != top:
                if colors.get(q) != color:
                    hide(q)
                else:
                    colors[q] = PURIFIED
                q = down[q]

        def unpurify(p: int, color: str, top: int) -> None:
            assert color == colors[p] and color is not None
            q = up[top]
            while q != top:
                if colors.get(q) is PURIFIED:
                    colors[q] = color
                else:
                    unhide(q)
                q = up[q]

        def choose_column() -> tuple[int, int]:
            c = right[0]
            best = -1
            min_size = math.inf
            while c != 0:
                if lengths[c] < min_size:
                    best, min_size = c, lengths[c]
                    if min_size == 0:
                        return c, 0
                c = right[c]
            return best, min_size

        return search_iterative()

    def create_data_structure(self) -> tuple[Any, ...]:
        all_constraints = Counter()
        colored_constraints = set()
        for name, constraints in self.constraints.items():
            this_rows_constraints = Counter()
            for constraint in constraints:
                if isinstance(constraint, tuple):
                    constraint, _ = constraint
                    colored_constraints.add(constraint)
                this_rows_constraints[constraint] += 1
            if any(value > 1 for value in this_rows_constraints.values()):
                dups = [
                    constraint
                    for constraint, value in this_rows_constraints.items()
                    if value > 1
                ]
                raise ValueError(f"Row {name} has duplicate constraints {dups}")
            all_constraints += this_rows_constraints
        if not colored_constraints <= self.optional_constraints:
            bad_constraints = colored_constraints - self.optional_constraints
            raise ValueError(f"Colored constraints must be optional: {bad_constraints}")
        primary_constraints = set(all_constraints.keys()) - self.optional_constraints
        secondary_constraints = {
            x for x in self.optional_constraints if all_constraints[x] > 1
        }
        if self.debug:
            print(
                f"There are {len(self.constraints)} rows; "
                f"{len(primary_constraints)} required constraints; "
                f"{len(secondary_constraints)} optional constraints;"
            )

        primary_length = len(primary_constraints)
        secondary_length = len(secondary_constraints)
        total_length = primary_length + secondary_length
        right = [*range(1, total_length + 2), 0]
        left = [total_length + 1, *range(total_length + 1)]
        right[primary_length] = 0
        left[0] = primary_length
        right[-1] = primary_length + 1
        left[primary_length + 1] = len(right) - 1
        lengths = [0] * (total_length + 2)

        constraints_iter = chain(
            sorted(primary_constraints), sorted(secondary_constraints))
        names = dict(enumerate(constraints_iter, start=1))
        names_map = {name: index for index, name in names.items()}
        spacer_indices = []
        constraints_length = sum(1 + len(x) for x in self.constraints.values()) + 1
        colors: dict[int, str | _Purified] = {}
        up = [*range(total_length + 2), *([0] * constraints_length)]
        down = up[:]
        top = [0] * len(up)
        current_index = total_length + 1

        def new_node(my_top: int) -> None:
            nonlocal current_index
            current_index += 1
            up[current_index] = my_top_previous_up = up[my_top]
            top[current_index] = down[current_index] = my_top
            up[my_top] = down[my_top_previous_up] = current_index
            if my_top:
                lengths[my_top] += 1

        for name, items in self.constraints.items():
            new_node(0)  # add a spacer node
            spacer_indices.append(current_index)
            names[current_index] = name
            for item in items:
                color = None
                if isinstance(item, tuple):
                    item, color = item
                if (my_top := names_map.get(item)) is None:
                    # A secondary constraint that only appeared once.  We can ignore.
                    continue
                new_node(my_top)
                if color:
                    colors[current_index] = color
        new_node(0)  # Add a final spacer
        current_index += 1
        up[current_index:] = down[current_index:] = top[current_index:] = []

        return left, right, lengths, up, down, top, colors, names, spacer_indices

    def __print_debug_info(
        self,
        depth: int,
        min_constraint: int,
        row: Row,
        index: int,
        count: int,
        visible_rows: int,
    ) -> None:
        indent = self.__indent(depth)
        if count == 1:
            print(f"{indent}• ", end="")
        else:
            print(f"{indent}{index}/{count} ", end="")
        print(f"{self.names[min_constraint]}: Row {row} ({visible_rows})")

    def get_name(self, index: int) -> str:
        spacer_index = bisect.bisect_right(self.spacer_indices, index) - 1
        next_smallest = self.spacer_indices[spacer_index]
        return self.names[next_smallest]

    @staticmethod
    def _default_row_printer(solution: Sequence[Row]) -> None:
        print(sorted(solution))

    @staticmethod
    @cache
    def __indent(depth: int) -> str:
        return " | " * depth

    def show(self, index: int, verbose=False) -> str:
        left, right, lengths, up, down, top = self.memory
        if index < len(left):
            if index == 0:
                return "ROOT"
            elif index == len(left) - 1:
                return "SECOND_ROOT"
            else:
                return self.names[index]
        else:
            spacer_index = bisect.bisect_right(self.spacer_indices, index) - 1
            spacer = self.spacer_indices[spacer_index]
            if spacer == index:
                result = f"<{self.names[spacer]}>"
                if not verbose:
                    return result
                items = []
                for ix in count(index + 1):
                    if top[ix] == 0:
                        break
                    name = self.names[top[ix]]
                    color = self.colors.get(ix)
                    if color:
                        name = f"{name}/{color}"
                    items.append(name)
                return result + ": " + ",".join(items)
            else:
                color = self.colors.get(index)
                if color:
                    return f"<{self.names[spacer]} {self.names[top[index]]}/{color}>"
                else:
                    return f"<{self.names[spacer]} {self.names[top[index]]}>"
