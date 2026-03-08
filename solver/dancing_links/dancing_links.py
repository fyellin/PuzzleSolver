from collections.abc import Callable, Hashable, Sequence
from typing import cast

from .dancing_links_common import (
    PURIFIED,
    DancingLinksBase,
    DLConstraint,
    DLData,
)


class DancingLinks[Row: Hashable](DancingLinksBase[Row]):
    data: DLData
    max_debugging_depth: int

    def __init__(
        self,
        constraints: dict[Row, list[DLConstraint]],
        *,
        row_printer: Callable[[Sequence[Row]], None] | None = None,
        optional_constraints: set[str] | None = None,
        check_solution: Callable[[Sequence[Row]], bool] | None = None,
        color: bool = True,
    ):
        """The entry to the Dancing Links code.  Constraints should be a dictionary.
        Each key is the name of the row (something meaningful to the user).
        The value should be a list/tuple of the row_to_constraints satisfied by this row.

        The row names and constraint names can be anything immutable and hashable.
        Typically, they are strings, but feel free to use whatever works best. Also,
        all constraint names must be "comparable" to each other. So strings really do work
        best
        """
        super().__init__(constraints, row_printer=row_printer,
                         optional_constraints=optional_constraints,
                         check_solution=check_solution, color=color)

    def inner_solve(self) -> tuple[int, int]:
        left, right, lengths, up, down, top, colors = (
            self.data.left, self.data.right, self.data.lengths,
            self.data.up, self.data.down, self.data.top, self.data.colors,
        )
        constraint_names = self.data.constraint_names
        visible_rows = len(self.data.row_names)

        def search_iterative() -> tuple[int, int]:
            steps = solutions = 0
            stack: list[list[int]] = [[1, 0, 0, 0]]

            while stack:
                depth, r, chosen_item, index = frame = stack.pop()
                if r > 0:
                    # r is the row before the one I want to scan.  If r == min_constraint,
                    # then this is the first row, and I don't have a row to uncover
                    if r != chosen_item:
                        uncover_row(r)

                    r = down[r]
                    # The next time we reach min_constraint, the column is exhausted.
                    if r == chosen_item:
                        uncover_item(chosen_item)
                        continue

                    cover_row(r)

                    frame[1], frame[3] = r, index + 1  # reuse previous frame.
                    stack.append(frame)
                    if depth <= self.max_debugging_depth:
                        self._print_debug_info(
                            depth, chosen_item, r, index,
                            lengths[chosen_item], visible_rows,
                        )
                        depth += lengths[chosen_item] != 1

                    # stack.append((depth, 0, 0, 0))
                    # Fall through

                steps += 1
                if right[0] == 0:
                    if depth <= self.max_debugging_depth:
                        self._print_solution(depth)
                    # There can't be any frames with r == 0.
                    solution = [s[1] for s in stack if s[1] != s[2]]
                    if self.check_solution(solution):
                        solutions += 1
                        self.row_printer([self.get_name(r) for r in solution])
                    continue

                chosen_item, feasible = choose_column()

                if not feasible:
                    if depth <= self.max_debugging_depth:
                        self._print_infeasible(depth, chosen_item)
                    continue

                cover_item(chosen_item)
                stack.append([depth, chosen_item, chosen_item, 1])
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

        def uncover_item(item: int) -> None:
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
                    j = uu  # go to previous spacer
                elif colors[j] is not PURIFIED:
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
                elif colors[j] is not PURIFIED:
                    lengths[tt] += 1
                    down[uu] = up[dd] = j
                j -= 1

        def commit_item(item: int, item_top: int) -> None:
            assert item_top == top[item]
            color = colors[item]
            if color is None:
                cover_item(item_top)
            elif color is not PURIFIED:
                purify(item, cast(str, color), item_top)

        def uncommit_item(item: int, item_top: int) -> None:
            assert item_top == top[item]
            color = colors[item]
            if color is None:
                uncover_item(item_top)
            elif color is not PURIFIED:
                unpurify(item, cast(str, color), item_top)

        def purify(_p: int, color: str, top: int) -> None:
            assert color == colors[_p] and color is not None
            q = down[top]
            while q != top:
                if colors[q] != color:
                    hide(q)
                else:
                    colors[q] = PURIFIED
                q = down[q]

        def unpurify(_p: int, color: str, top: int) -> None:
            assert color == colors[_p] and color is not None
            q = up[top]
            while q != top:
                if colors[q] is PURIFIED:
                    colors[q] = color
                else:
                    unhide(q)
                q = up[q]

        def choose_column() -> tuple[int, bool]:
            """Return (column, feasible) using MRV with a non-sharp preference.

            Columns whose names start with '#' are deferred: they are only chosen
            when their length is 0 (infeasible — must prune) or 1 (forced — no real
            branch), or when every remaining column is a sharp column with length > 1.
            Among eligible columns the standard MRV (fewest rows) applies.
            """
            c = right[0]
            best = -1
            min_size = float('inf')
            preferred = -1      # best non-sharp, or sharp with length <= 1
            preferred_min = float('inf')
            while c != 0:
                size = lengths[c]
                if size < min_size:
                    best, min_size = c, size
                    if min_size == 0:
                        return c, False
                if size < preferred_min and (size <= 1 or not constraint_names[c].startswith('#')):
                    preferred, preferred_min = c, size
                c = right[c]
            return (preferred, True) if preferred != -1 else (best, True)

        return search_iterative()

    def create_data_structure(self) -> DLData:
        return self._build_dl_data(
            self.constraints,
            optional_constraints=self.optional_constraints,
            debug=self.debug,
        )
