import bisect
from collections import Counter
from collections.abc import Callable, Hashable, Sequence
from datetime import datetime
from functools import cache
from itertools import chain, count
from typing import Final, NamedTuple


class _Purified:
    __slots__ = ()


PURIFIED: Final = _Purified()

type DLConstraint = str | tuple[str, str]


class DLData(NamedTuple):
    left: list[int]
    right: list[int]
    lengths: list[int]
    up: list[int]
    down: list[int]
    top: list[int]
    colors: dict[int, str | _Purified]
    names: dict[int, str]
    spacer_indices: list[int]


class DancingLinks[Row: Hashable]:
    constraints: dict[Row, list[DLConstraint]]
    optional_constraints: set[str]
    row_printer: Callable[[Sequence[Row]], None] | None
    check_solution: Callable[[Sequence[Row]], bool]
    data: DLData
    debug: bool
    max_debugging_depth: int

    def __init__(
        self,
        constraints: dict[Row, list[DLConstraint]],
        *,
        row_printer: Callable[[Sequence[Row]], None] | None = None,
        optional_constraints: set[str] | None = None,
        check_solution: Callable[[Sequence[Row]], bool] | None = None,
    ):
        """The entry to the Dancing Links code.  Constraints should be a dictionary.
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
        self.check_solution = check_solution or (lambda _: True)

    def solve(self, debug: int | None = 0) -> None:
        time1 = datetime.now()
        self.debug = debug is not None
        self.max_debugging_depth = debug if debug is not None else -1

        self.data = self.create_data_structure()
        steps, solutions = self.inner_solve()

        time2 = datetime.now()
        print("Steps =", steps)
        print("Solutions =", solutions)
        print("Time =", (time2 - time1))

    def inner_solve(self) -> tuple[int, int]:
        left, right, lengths, up, down, top, colors = (
            self.data.left, self.data.right, self.data.lengths,
            self.data.up, self.data.down, self.data.top, self.data.colors,
        )
        visible_rows = len(self.data.spacer_indices)

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
                        self.__print_debug_info(
                            depth, chosen_item, self.get_name(r), index,
                            lengths[chosen_item], visible_rows,
                        )
                        depth += lengths[chosen_item] != 1

                    # stack.append((depth, 0, 0, 0))
                    # Fall through

                steps += 1
                if right[0] == 0:
                    if depth <= self.max_debugging_depth:
                        print(f"{self.__indent(depth)}✓ SOLUTION")
                    # There can't be any frames with r == 0.
                    solution = [s[1] for s in stack if s[1] != s[2]]
                    if self.check_solution(solution):
                        solutions += 1
                        self.row_printer([self.get_name(r) for r in solution])
                    continue

                chosen_item, feasible = choose_column()

                if not feasible:
                    if depth <= self.max_debugging_depth:
                        name = self.data.names[chosen_item]
                        print(f"{self.__indent(depth)}✕ {name}")
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
                    j = uu  # go to previous spacer
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

        def choose_column() -> tuple[int, bool]:
            """
            Returns constraint, feasible
            """
            c = right[0]
            best = -1
            min_size = 1_000_000_000
            while c != 0:
                if lengths[c] < min_size:
                    best, min_size = c, lengths[c]
                    if min_size == 0:
                        return c, False
                c = right[c]
            return best, True

        return search_iterative()

    def create_data_structure(self) -> DLData:
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
                duplicates = [k for k, v in this_rows_constraints.items() if v > 1]
                raise ValueError(f"Row {name} has duplicate constraints {duplicates}")
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
        down = up.copy()
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
                    # A secondary constraint that only appeared once.  We can delete it.
                    continue
                new_node(my_top)
                if color is not None:
                    colors[current_index] = color
        new_node(0)  # Add a final spacer
        current_index += 1
        up[current_index:] = down[current_index:] = top[current_index:] = []

        return DLData(left, right, lengths, up, down, top, colors, names, spacer_indices)

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
        print(f"{self.data.names[min_constraint]}: Row {row} ({visible_rows})")

    def get_name(self, index: int) -> str:
        spacer_index = bisect.bisect_right(self.data.spacer_indices, index) - 1
        next_smallest = self.data.spacer_indices[spacer_index]
        return self.data.names[next_smallest]

    @staticmethod
    def _default_row_printer(solution: Sequence[Row]) -> None:
        print(sorted(solution))

    @staticmethod
    @cache
    def __indent(depth: int) -> str:
        return " | " * depth

    def show(self, index: int, verbose=False) -> str:
        left, right, lengths, up, down, top, colors, names, spacer_indices = self.data
        if index < len(left):
            if index == 0:
                return "ROOT"
            elif index == len(left) - 1:  # noqa
                return "SECOND_ROOT"
            else:
                return names[index]
        else:
            spacer_index = bisect.bisect_right(spacer_indices, index) - 1
            spacer = spacer_indices[spacer_index]
            if spacer == index:
                result = f"<{names[spacer]}>"
                if not verbose:
                    return result
                items = []
                for ix in count(index + 1):
                    if top[ix] == 0:
                        break
                    name = names[top[ix]]
                    color = colors.get(ix)
                    if color:
                        name = f"{name}/{color}"
                    items.append(name)
                return result + ": " + ",".join(items)
            else: # noqa
                color = colors.get(index)
                if color:
                    return f"<{names[spacer]} {names[top[index]]}/{color}>"
                else:
                    return f"<{names[spacer]} {names[top[index]]}>"


def get_row_column_optional_constraints(rows: int, columns: int) -> set[DLConstraint]:
    return {f"r{r}c{c}" for r in range(1, rows + 1) for c in range(1, columns + 1)}
