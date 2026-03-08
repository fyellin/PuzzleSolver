from __future__ import annotations

import copy
import os
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from collections.abc import Callable, Hashable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from itertools import chain, count
from typing import Final, cast

from rich import print as rprint
from rich.markup import escape
from rich.table import Table

RUNNING_PYTEST = "PYTEST_CURRENT_TEST" in os.environ


class _Purified:
    __slots__ = ()


PURIFIED: Final = _Purified()

type DLConstraint = str | tuple[str, str]


@dataclass
class DLData:
    """Unified DLX data structure shared by both solver classes.

    Construction-time metadata (names_map, primary_length, total_length) is retained so
    that DancingLinksBounds.create_data_structure can populate bound/slack without
    re-deriving it. Variables "bound" and "slack" are only populated by DancingLinksBounds;
    DancingLinks leaves them empty.
    """
    # Header nodes: indices 1..primary_length are primary items;
    # primary_length+1..total_length are secondary items.
    # Index 0 is the primary root; index primary_length+1 is the secondary root.
    # left[i]/right[i]: doubly-linked list threading the active header nodes.
    left: list[int]
    right: list[int]
    # lengths[i]: number of rows currently visible in column i.
    lengths: list[int]
    # up[i]/down[i]: doubly-linked circular list for each column.
    # For a header node h: down[h] is the first data node, up[h] is the last.
    up: list[int]
    down: list[int]
    # top[i]: for a data node, the index of its column header.
    #         for a spacer node, 0 (the spacer sentinel value).
    top: list[int]
    # colors[i]: for secondary-item data nodes, the color string assigned to that node,
    #   PURIFIED once the color has been committed and other nodes checked, or None for
    #   primary-item data nodes and secondary nodes that appear without a color.
    colors: list[str | _Purified | None]
    # constraint_names[i]: the name of primary/secondary header node i (indices 1..total_length).
    #   Index 0 is unused (empty string placeholder for the root node).
    constraint_names: list[str]
    # row_names: maps each spacer node index to the row name (any Hashable).
    #   The keys are exactly the spacer node indices, in ascending order.
    row_names: dict[int, Hashable]
    # Construction-time metadata retained for DancingLinksBounds.create_data_structure.
    names_map: dict[str, int]
    # Number of primary items (indices 1..primary_length in the header list).
    primary_length: int
    total_length: int
    # bound[i]: counts down from hi[i] as rows covering item i are selected.
    #   Starts at hi[i]. Decremented each time a row covering i is selected.
    #   When bound[i] == slack[i]: lower bound met (lo rows selected); i leaves
    #     the active list.
    #   When bound[i] == 0: upper bound hi reached; remaining rows are hidden.
    bound: list[int] = field(default_factory=list)
    # slack[i] = hi[i] - lo[i]: how many extra coverages (beyond lo) are allowed.
    #   slack[i] == 0 means exact cover (lo == hi).
    slack: list[int] = field(default_factory=list)


class DancingLinksBase[Row: Hashable](ABC):
    """Shared helpers inherited by both solver classes.

    Provides display/debug utilities, the core DLX data-structure builder, and
    solution verification.  Subclasses supply the concrete "data" attribute and
    the "inner_solve()" / "create_data_structure()" methods.
    """

    data: DLData
    constraints: dict[Row, list[DLConstraint]]
    optional_constraints: set[str]
    row_printer: Callable[[Sequence[Row]], None]
    check_solution: Callable[[Sequence[Row]], bool]
    debug: bool
    color: bool

    @abstractmethod
    def create_data_structure(self) -> DLData: ...

    @abstractmethod
    def inner_solve(self) -> tuple[int, int]: ...

    def __init__(
        self,
        constraints: dict[Row, list[DLConstraint]],
        *,
        row_printer: Callable[[Sequence[Row]], None] | None = None,
        optional_constraints: set[str] | None = None,
        check_solution: Callable[[Sequence[Row]], bool] | None = None,
        color: bool = False,
    ) -> None:
        self.constraints = constraints
        self.optional_constraints = optional_constraints or set()
        self.row_printer = row_printer or self._default_row_printer
        self.check_solution = check_solution or (lambda _: True)
        self.max_debugging_depth = -1
        self.debug = False
        self.color = color

    def solve(self, debug: bool = False, max_debug_depth: int | None = None) -> None:
        time1 = datetime.now()
        self.debug = debug
        self.max_debugging_depth = -1 if not debug else (max_debug_depth or 1000)

        self.data = self.create_data_structure()
        saved_copy = copy.deepcopy(self.data) if RUNNING_PYTEST else None
        steps, solutions = self.inner_solve()
        if saved_copy is not None:
            assert saved_copy == self.data, "Data structure changed during solve"

        self._print_solve_summary(steps, solutions, datetime.now() - time1)

    # ------------------------------------------------------------------
    # Data-structure construction
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_and_partition_constraints(
        constraints: dict[Hashable, list[DLConstraint]],
        optional_constraints: set[str],
    ) -> tuple[Counter[str], set[str], set[str], set[str]]:
        """Validate input constraints and split them into primary vs. secondary."""
        all_constraints_count: Counter[str] = Counter()
        colored_constraints: set[str] = set()

        for row_name, row_constraints in constraints.items():
            this_rows_constraints: Counter[str] = Counter()
            for constraint in row_constraints:
                if isinstance(constraint, tuple):
                    constraint_name, _color = constraint
                    colored_constraints.add(constraint_name)
                else:
                    constraint_name = constraint
                this_rows_constraints[constraint_name] += 1

            duplicates = [k for k, v in this_rows_constraints.items() if v > 1]
            if duplicates:
                # Message is relied upon by tests looking for "duplicate"
                raise ValueError(f"Row {row_name!r} has duplicate constraints {duplicates}")
            all_constraints_count += this_rows_constraints

        if not colored_constraints <= optional_constraints:
            bad_constraints = colored_constraints - optional_constraints
            # Message is relied upon by tests looking for "optional"
            raise ValueError(f"Colored constraints must be optional: {bad_constraints}")

        primary_constraints = set(all_constraints_count.keys()) - optional_constraints
        secondary_constraints = {x for x in optional_constraints if all_constraints_count[x] > 1}
        return (all_constraints_count, colored_constraints,
                primary_constraints, secondary_constraints)

    @staticmethod
    def _build_dl_data(
        constraints: dict[Hashable, list[DLConstraint]],
        *,
        optional_constraints: set[str],
        debug: bool = False,
    ) -> DLData:
        """Build the shared DLX linked-list structure (without bounds arrays)."""
        (
            all_constraints,
            _colored_constraints,
            primary_constraints,
            secondary_constraints,
        ) = DancingLinksBase._validate_and_partition_constraints(constraints, optional_constraints)

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

        constraints_length = sum(1 + len(x) for x in constraints.values()) + 1

        constraint_names: list[str] = [
            '', *chain(sorted(primary_constraints), sorted(secondary_constraints))
        ]
        names_map = {name: i for i, name in enumerate(constraint_names) if i > 0}
        row_names: dict[int, Hashable] = {}

        up = [*range(total_length + 2), *([0] * constraints_length)]
        down = up.copy()
        top = [0] * len(up)
        colors: list[str | _Purified | None] = [None] * len(up)
        current_index = total_length + 1

        def new_node(my_top: int) -> None:
            nonlocal current_index
            current_index += 1
            up[current_index] = prev_up = up[my_top]
            top[current_index] = down[current_index] = my_top
            up[my_top] = down[prev_up] = current_index
            if my_top:
                lengths[my_top] += 1

        for row_name, row_items in constraints.items():
            new_node(0)  # spacer node
            row_names[current_index] = row_name

            for item in row_items:
                color: str | None = None
                if isinstance(item, tuple):
                    item_name, color = item
                else:
                    item_name = item

                my_top = names_map.get(item_name)
                if my_top is None:
                    # A secondary constraint that only appeared once — skip it.
                    continue

                new_node(my_top)
                if color is not None:
                    colors[current_index] = color

        new_node(0)  # final spacer
        current_index += 1
        up[current_index:] = down[current_index:] = []
        top[current_index:] = colors[current_index:] = []

        if debug:
            dropped_0 = sum(1 for x in optional_constraints if all_constraints[x] == 0)
            dropped_1 = sum(1 for x in optional_constraints if all_constraints[x] == 1)
            table = Table(show_header=False, highlight=True)
            table.add_column(style="bold")
            table.add_column(justify="right")
            table.add_row("Rows", str(len(constraints)))
            table.add_row("Required constraints", str(len(primary_constraints)))
            table.add_row("Optional constraints kept", str(len(secondary_constraints)))
            table.add_row("Optional constraints dropped (0 appearances)", str(dropped_0))
            table.add_row("Optional constraints dropped (1 appearance)", str(dropped_1))
            rprint(table)

        return DLData(
            left=left,
            right=right,
            lengths=lengths,
            up=up,
            down=down,
            top=top,
            colors=colors,
            constraint_names=constraint_names,
            row_names=row_names,
            names_map=names_map,
            primary_length=primary_length,
            total_length=total_length,
        )

    # ------------------------------------------------------------------
    # Display / debug helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _default_row_printer(solution: Sequence) -> None:
        print(sorted(solution))

    @staticmethod
    @cache
    def _indent(depth: int) -> str:
        return " | " * (depth - 1)

    def get_name(self, index: int) -> Row:
        """Return the row name for the row whose spacer node is at or before "index". """
        spacer = next(k for k in range(index, -1, -1) if k in self.data.row_names)
        return self.data.row_names[spacer]

    def _print_solution(self, depth: int) -> None:
        if self.color:
            rprint(f"{self._indent(depth)}[green]✓ SOLUTION[/green]")
        else:
            print(f"{self._indent(depth)}✓ SOLUTION")

    def _print_infeasible(self, depth: int, chosen_item: int) -> None:
        name = self.data.constraint_names[chosen_item]
        if self.color:
            rprint(f"{self._indent(depth)}[red]✕ {escape(name)}[/red]")
        else:
            print(f"{self._indent(depth)}✕ {name}")

    def _print_debug_info(
            self,
            depth: int, chosen_item: int, r: int, index: int, n_rows: int, visible_rows: int,
            lo: int = 1, hi: int = 1,
    ) -> None:
        indent = self._indent(depth)
        name = self.data.constraint_names[chosen_item]
        row = self.get_name(r)
        prefix = "• " if n_rows == 1 else f"{index}/{n_rows} "
        if self.color:
            bounds = f"[cyan]⟨{lo}…{hi}⟩[/cyan]" if not (lo == 1 and hi == 1) else ""
            rprint(f"{indent}{prefix}[yellow]{escape(name)}[/yellow]{bounds}: "
                   f"Row {escape(str(row))} ({visible_rows})")
        else:
            bounds = f"⟨{lo}…{hi}⟩" if not (lo == 1 and hi == 1) else ""
            print(f"{indent}{prefix}{name}{bounds}: Row {row} ({visible_rows})")

    def _print_null_move(
            self,
            depth: int, chosen_item: int, index: int, n_rows: int, visible_rows: int,
            lo: int = 1, hi: int = 1,
    ) -> None:
        indent = self._indent(depth)
        name = self.data.constraint_names[chosen_item]
        prefix = "• " if n_rows == 1 else f"{index}/{n_rows} "
        if self.color:
            bounds = f"[cyan]⟨{lo}…{hi}⟩[/cyan]" if not (lo == 1 and hi == 1) else ""
            rprint(f"{indent}{prefix}[yellow][strike]{escape(name)}[/strike][/yellow]{bounds}: ε ({visible_rows})")
        else:
            bounds = f"⟨{lo}…{hi}⟩" if not (lo == 1 and hi == 1) else ""
            print(f"{indent}{prefix}{name}{bounds}: ε ({visible_rows})")

    def _print_solve_summary(self, steps: int, solutions: int, elapsed) -> None:
        table = Table(show_header=False, highlight=self.color)
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Solutions", str(solutions))
        table.add_row("Steps", str(steps))
        table.add_row("Time", str(elapsed))
        rprint(table)

    def show(self, index: int, verbose: bool = False, color: bool | None = None) -> str:
        """Return a human-readable description of node "index"."""
        color = self.color if color is None else color
        left, top, colors = self.data.left, self.data.top, self.data.colors
        constraint_names = self.data.constraint_names
        row_names = self.data.row_names

        def _item_str(ix: int) -> str:
            name = constraint_names[top[ix]]
            dlx_color = colors[ix]
            if dlx_color and not isinstance(dlx_color, _Purified):
                name = f"{name}/{dlx_color}"
            return name

        if index < len(left):
            if index == 0:
                label = "ROOT"
            elif index == len(left) - 1:
                label = "SECOND_ROOT"
            else:
                label = constraint_names[index]
            return f"\033[2m{label}\033[0m" if color else label

        spacer = next(k for k in range(index, -1, -1) if top[k] == 0)
        row_name = row_names.get(spacer, "<FINAL SPACER>")
        if not verbose:
            if spacer == index:
                return f"\033[35m<{row_name}>\033[0m" if color else f"<{row_name}>"
            item = _item_str(index)
            if color:
                return f"\033[35m<{row_name}\033[0m \033[33m{item}\033[35m>\033[0m"
            return f"<{row_name} {item}>"

        # verbose: all items in the row, with the item at index marked in brackets
        items = []
        for ix in count(spacer + 1):
            if top[ix] == 0:
                break
            name = _item_str(ix)
            if ix == index:
                name = f"\033[32m{name}\033[0m" if color else f"[{name}]"
            elif color:
                name = f"\033[33m{name}\033[0m"
            items.append(name)
        row_label = f"\033[35m<{row_name}>\033[0m" if color else f"<{row_name}>"
        return row_label + ": " + ", ".join(items)


def verify_solution(
    solution: Iterable[Hashable],
    constraints: dict[Hashable, list[DLConstraint]],
    optional_constraints: set[str],
    bounds: dict[str, tuple[int, int]],
) -> None:
    """Verify that a proposed solution satisfies all constraints.

    Checks:
    - Every primary item is covered lo..hi times (default 1..1 for items
      absent from bounds), including items never covered by the solution.
    - Every secondary item that appears uncolored does so at most once.
    - Every secondary item that appears colored does so with a single
      consistent color across all selected rows.
    - No secondary item appears both colored and uncolored.

    Prints an ERROR line for each violation found, then raises ValueError.
    """
    # Count coverage from selected rows.
    primary_coverage: Counter[str] = Counter()
    secondary_colors: defaultdict[str, set[str]] = defaultdict(set)
    secondary_uncolored: Counter[str] = Counter()
    for row_name in solution:
        for item in constraints[row_name]:
            if isinstance(item, tuple):
                item_name, color = item
                secondary_colors[item_name].add(color)
            elif item in optional_constraints:
                secondary_uncolored[item] += 1
            else:
                primary_coverage[item] += 1

    # Determine all primary items across the full constraint dict so that
    # items with zero coverage are also checked.
    all_primary = {
        # cast shouldn't be necessary, but PyCharm is confused.
        cast(str, item) for row_items in constraints.values()
        for item in row_items
        if not isinstance(item, tuple) and item not in optional_constraints
    }

    error = False

    for item_name in all_primary:
        coverage = primary_coverage[item_name]
        lo, hi = bounds.get(item_name, (1, 1))
        if not lo <= coverage <= hi:
            error = True
            print(f"ERROR: {item_name} covered {coverage} times; expected [{lo}, {hi}]")

    for item_name in set(secondary_colors) | set(secondary_uncolored):
        colors = secondary_colors[item_name]
        n_uncolored = secondary_uncolored[item_name]
        if n_uncolored > 1:
            error = True
            print(f"ERROR: {item_name} appears uncolored {n_uncolored} times (max 1)")
        elif n_uncolored == 1 and colors:
            error = True
            print(f"ERROR: {item_name} appears both uncolored and with colors {colors}")
        elif len(colors) > 1:
            error = True
            print(f"ERROR: {item_name} has multiple colors {colors}")

    if error:
        raise ValueError("Solution is invalid")


def get_row_column_optional_constraints(
        rows: int, columns: int, prefix: str = "", suffix: str = ""
) -> set[str]:
    return {f"{prefix}r{r}c{c}{suffix}" for r in range(1, rows + 1) for c in range(1, columns + 1)}
