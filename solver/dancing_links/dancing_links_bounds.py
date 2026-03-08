from __future__ import annotations

from collections.abc import Callable, Hashable, Sequence

from .dancing_links_common import (
    PURIFIED,
    DancingLinksBase,
    DLConstraint,
    DLData,
)


class DancingLinksBounds[Row: Hashable](DancingLinksBase[Row]):
    """Dancing Links implementing Knuth's Algorithm M (exact cover with multiplicities
    and colors).

    Primary items have bounds (lo, hi) specifying how many times they must be covered.
    Secondary items support color constraints (as in Algorithm C).
    When lo=hi=1 for all primary items and no colors are used, this reduces to
    Algorithm X.

    Constraints are specified as:
      - "item_name"              -> primary item (exact cover, or bounds from `bounds=`)
      - ("item_name", color)     -> secondary item with color (string color value)

    Multiplicity bounds for primary items are given via the `bounds` constructor
    argument: bounds={"item_name": (lo, hi)}.  Items not in `bounds` default to (1, 1).
    """

    bounds: dict[str, tuple[int, int]]
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
        bounds: dict[str, tuple[int, int]] | None = None,
    ):
        super().__init__(constraints, row_printer=row_printer,
                         optional_constraints=optional_constraints,
                         check_solution=check_solution, color=color)
        self.bounds = bounds or {}

    def inner_solve(self) -> tuple[int, int]:
        # Unpack all arrays into locals for speed — avoids attribute lookups in the
        # hot inner loop.
        left, right, lengths, up, down, top, bound, slack, colors = (
            self.data.left,
            self.data.right,
            self.data.lengths,
            self.data.up,
            self.data.down,
            self.data.top,
            self.data.bound,
            self.data.slack,
            self.data.colors,
        )
        constraint_names = self.data.constraint_names
        total_length = self.data.total_length
        # visible_rows tracks the number of rows not currently hidden; used only for
        # debug output.
        visible_rows = len(self.data.row_names)

        def search_iterative() -> tuple[int, int]:
            # Each stack frame is [depth, r, chosen_item, ft, index].
            #   depth:        recursion depth, used for debug indentation.
            #   r:            data node currently being tried, or chosen_item (sentinel)
            #                 for level-entry frames and null-move frames.
            #   chosen_item:  column header we are branching on.
            #   ft:           >=0 normal frame:
            #                   0  = full-cover mode (cover_full called, slack==0).
            #                   >0 = tweaking mode; ft = down[chosen_item] at entry
            #                        (the first option that will be tweaked/spliced).
            #                 <0  null-move sentinel: ft_orig = -ft is the original ft.
            #   index:        1-based count of options tried so far (for debug output).
            # Bootstrap frame [1, 0, 0, 0, 0]: r=0 skips the backdown/advance block.
            steps = solutions = 0
            stack: list[list[int]] = [[1, 0, 0, 0, 0]]

            while stack:
                depth, r, chosen_item, ft, index = frame = stack.pop()

                if r > 0:
                    if ft < 0:
                        # --- Null-move return ---
                        # ft encodes -ft_orig (the original first-tweak pointer).
                        ft_orig = -ft
                        # Reactivate chosen_item if only the null-move deactivated it
                        # (bound != 0 means cover_full was not called at entry).
                        if bound[chosen_item] != 0:
                            ll, rr = left[chosen_item], right[chosen_item]
                            right[ll] = left[rr] = chosen_item
                        # Collect tweaked rows before restore_tweaked clears their
                        # PURIFIED marks.  Only done when bound != 0 (bound == 0 means
                        # cover_full at entry already hid these rows; no extra hide was done).
                        tweaked_rows: list[int] = []
                        if bound[chosen_item] != 0:
                            x = ft_orig
                            while x != chosen_item and colors[x] is PURIFIED:
                                tweaked_rows.append(x)
                                x = down[x]
                        # Restore all options tweaked at this level.
                        restore_tweaked(chosen_item, ft_orig)
                        # Unhide tweaked rows in reverse (undo the hide done at entry).
                        for row in reversed(tweaked_rows):
                            unhide(row)
                        # Undo cover_full if it was called at level entry (bound == 0).
                        if bound[chosen_item] == 0:
                            uncover_full(chosen_item, react=True)
                        bound[chosen_item] += 1
                        continue

                    # Undo the previous option if one was tried.
                    if r != chosen_item:
                        if ft == 0:
                            # Full-cover: restore r back into chosen_item's column.
                            uncover_row(r, chosen_item)
                        else:
                            # Tweaking: uncommit r's row items; r stays spliced so it
                            # cannot be re-selected at a deeper level.
                            uncommit_row(r, chosen_item)

                    # Advance to the next option.
                    if ft == 0: # noqa
                        # Full-cover: follow r's stable original pointer (r was restored).
                        r = down[r]
                    else:
                        # Tweaking: take the current top of the column (first un-tweaked).
                        r = down[chosen_item]

                    if r == chosen_item:
                        # Column exhausted.
                        if ft != 0 and bound[chosen_item] < slack[chosen_item]:
                            # Tweaking mode, lower bound already met (prior coverages >= lo):
                            # try the null move
                            # (choose nothing for chosen_item at this level).
                            # When cover_full was NOT called at entry (bound != 0), hide
                            # every tweaked row from all other columns.  This prevents
                            # other items in the null-move sub-search from selecting a
                            # previously-tried row and producing a duplicate solution.
                            # (When bound == 0, cover_full already hid those rows.)
                            if bound[chosen_item] != 0:
                                stop = down[chosen_item]
                                x = ft
                                while x != stop:
                                    hide(x)
                                    x = down[x]
                                ll, rr = left[chosen_item], right[chosen_item]
                                left[rr], right[ll] = ll, rr
                            # Encode ft into the sentinel so restore_tweaked can recover it.
                            stack.append([depth, chosen_item, chosen_item, -ft, index + 1])
                            # Fall through to choose_item for the null-move sub-search.
                            if depth <= self.max_debugging_depth:
                                # Each committed row increments frame[4], so index
                                # is already N+1 here (N rows tried + this null-move
                                # = N+1 total options, and index==N+1 naturally).
                                n_rows = lengths[chosen_item] + index
                                # Only print the null-move when it is a genuine branch
                                # (n_rows > 1 means at least one row was also tried at
                                # this level).  A forced null-move (column was empty)
                                # has n_rows==1 and adds no information.
                                if n_rows > 1:
                                    hi = bound[chosen_item] + 1   # pre-decrement value
                                    lo = max(0, hi - slack[chosen_item])
                                    self._print_null_move(
                                        depth, chosen_item, index, n_rows, visible_rows, lo, hi,
                                    )
                                depth += n_rows > 1
                        else:
                            # Backup: restore tweaked nodes, undo entry effects.
                            if ft != 0:
                                restore_tweaked(chosen_item, ft)
                            if bound[chosen_item] == 0:
                                uncover_full(chosen_item, react=True)
                            bound[chosen_item] += 1
                            continue
                    else:
                        # Try this option.
                        cover_row(r, chosen_item)
                        # Early prune: if chosen_item is still active and θ=0
                        # (not enough rows remain to meet the lower bound), skip
                        # this option without going deeper.  Equivalent to what
                        # choose_item would detect one step later, but avoids the
                        # extra stack frame and keeps the debug count accurate.
                        lo_eff = max(bound[chosen_item] - slack[chosen_item], 0)
                        if lo_eff > 0 and lengths[chosen_item] < lo_eff:
                            uncommit_row(r, chosen_item)
                            frame[1] = chosen_item  # sentinel: nothing committed
                            frame[4] = index + 1
                            stack.append(frame)
                            continue
                        frame[1], frame[4] = r, index + 1
                        stack.append(frame)
                        if depth <= self.max_debugging_depth:
                            # Display lo/hi use pre-decrement bound (bound+1) so the
                            # label reflects the item's bounds before this level entry.
                            hi = bound[chosen_item] + 1
                            lo = max(0, hi - slack[chosen_item])
                            if ft == 0:
                                # Full-cover: uncover_row restores the previous row before
                                # each try, so lengths is always N-1 at print time.
                                n_rows = lengths[chosen_item] + 1
                            else:
                                # n_rows uses the post-decrement bound (distinct from lo).
                                # bound < slack (null-move possible): N+1 total options.
                                # bound == slack (no null-move): N options exactly.
                                # bound > slack (must-cover): N - (bound-slack) options
                                #   (infeasible tail is pruned before reaching the stack).
                                lo_nrows = max(0, bound[chosen_item] - slack[chosen_item])
                                n_rows = (lengths[chosen_item] + index
                                          + int(bound[chosen_item] < slack[chosen_item])
                                          - lo_nrows)
                            self._print_debug_info(
                                depth, chosen_item, r, index, n_rows, visible_rows, lo, hi,
                            )
                            depth += n_rows > 1

                steps += 1
                if right[0] == 0:
                    # Active primary list is empty — all items are satisfied.
                    if depth <= self.max_debugging_depth:
                        self._print_solution(depth)
                    # Data nodes have index > total_length + 1; level-entry and null-move
                    # frames carry a header index (<= total_length + 1) and are excluded.
                    solution = [s[1] for s in stack if s[1] > total_length + 1]
                    named = [self.get_name(node) for node in solution]
                    if self.check_solution(named):
                        solutions += 1
                        self.row_printer(named)
                    continue

                chosen_item, feasible = choose_item()

                if not feasible:
                    if depth <= self.max_debugging_depth:
                        self._print_infeasible(depth, chosen_item)
                    continue

                # Enter a new level for chosen_item (Algorithm M level entry).
                bound[chosen_item] -= 1
                if bound[chosen_item] == 0 and slack[chosen_item] == 0:
                    # Full-cover mode: lo == hi, upper bound just reached.
                    cover_full(chosen_item)
                    ft = 0
                else:
                    # Tweaking mode: item stays active unless bound hit 0.
                    ft = down[chosen_item]   # first option (= first_tweak)
                    if bound[chosen_item] == 0:
                        cover_full(chosen_item)
                stack.append([depth, chosen_item, chosen_item, ft, 1])

            return steps, solutions

        def cover_row(r: int, chosen_item: int) -> None:
            """Add row r to the current partial solution.

            Removes r from chosen_item's column (so the same row-node can't be
            re-selected if chosen_item's bound still needs more coverage), then
            processes every other item j in the row via commit_item.

            commit_item(j) either covers j's column header (primary items) or
            enforces a color constraint (secondary colored items).
            """
            # Remove r from chosen_item's column so we don't revisit it.
            uu, dd = up[r], down[r]
            up[dd], down[uu] = uu, dd
            lengths[chosen_item] -= 1
            # Mark r's node PURIFIED so hide() skips it if called while r's
            # up/down pointers are stale (e.g. during a color tweak on another
            # item in the same row when in tweaking mode).
            colors[r] = PURIFIED

            # Walk the other items in the row (j wraps around using the spacer at j==r).
            j = r + 1
            while j != r:
                tt = top[j]
                if tt <= 0:
                    # Spacer node: jump back to the start of the previous row.
                    j = up[j]
                else:
                    if tt != chosen_item:
                        commit_item(j, tt)
                j += 1

        def uncover_row(r: int, chosen_item: int) -> None:
            """Undo cover_row — exact reverse, items uncommitted in reverse order."""
            j = r - 1
            while j != r:
                tt = top[j]
                if tt <= 0:
                    j = down[j]
                else:
                    if tt != chosen_item:
                        uncommit_item(j, tt)
                j -= 1

            # Clear the PURIFIED mark before restoring r to chosen_item's column.
            colors[r] = None
            uu, dd = up[r], down[r]
            down[uu] = up[dd] = r
            lengths[chosen_item] += 1

        def uncommit_row(r: int, chosen_item: int) -> None:
            """Uncommit items in r's row without restoring r to chosen_item's column.

            Used in tweaking mode when advancing to the next option: undo the
            commits made by cover_row for all items except chosen_item, but leave
            r spliced out of chosen_item's column so it cannot be re-selected at
            a deeper level (preventing duplicate solutions).
            """
            j = r - 1
            while j != r:
                tt = top[j]
                if tt <= 0:
                    j = down[j]
                else:
                    if tt != chosen_item:
                        uncommit_item(j, tt)
                j -= 1
            # r remains spliced out of chosen_item's column (no column restore).

        def restore_tweaked(chosen_item: int, ft: int) -> None:
            """Restore all options tweaked at this level back into chosen_item's column.

            At cover_row time each option was spliced out of chosen_item's column
            (up/down pointers of its neighbors updated).  We restore them in
            forward order (ft toward the current top of the column), using each
            node's still-valid up/down pointers to find its neighbors.
            """
            stop = down[chosen_item]
            x = ft
            while x != stop:
                next_x = down[x]
                colors[x] = None  # clear the PURIFIED mark set by cover_row
                uu, dd = up[x], down[x]
                down[uu] = x
                up[dd] = x
                lengths[chosen_item] += 1
                x = next_x

        def cover_full(item: int) -> None:
            """Remove item from the active list and hide all rows in its column.

            Called when bound[item] reaches 0 (upper bound hi reached). After
            this call item is absent from the active list and every row in its
            column is hidden from all other items' columns.
            """
            ll, rr = left[item], right[item]
            left[rr], right[ll] = ll, rr
            row = down[item]
            while row != item:
                hide(row)
                row = down[row]

        def uncover_full(item: int, react: bool) -> None:
            """Reverse of cover_full.

            Unhides all rows in item's column (bottom-to-top). If react is True,
            also restores item to the active list. Pass react=False when the
            caller reactivates item manually (e.g. after a null-move cleanup
            where the deactivation was done without calling cover_full).
            """
            row = up[item]
            while row != item:
                unhide(row)
                row = up[row]
            if react:
                ll, rr = left[item], right[item]
                right[ll] = left[rr] = item

        def hide(row: int) -> None:
            """Remove row from every column except the one we're currently branching on.

            The node for the chosen_item is not visited here (we start at row+1, which
            is the first non-spacer item of the row, not the chosen_item node itself).
            This keeps the chosen_item's column intact so we can still iterate over it.
            """
            nonlocal visible_rows
            visible_rows -= 1
            j = row + 1
            while j != row:
                tt, uu, dd = top[j], up[j], down[j]
                if tt <= 0:
                    j = uu  # spacer: jump to start of previous row
                elif colors[j] is not PURIFIED:
                    # Splice j out of its column's circular list and decrement the count.
                    up[dd], down[uu] = uu, dd
                    lengths[tt] -= 1
                j += 1

        def unhide(row: int) -> None:
            """Exact reverse of hide."""
            nonlocal visible_rows
            visible_rows += 1
            j = row - 1
            while j != row:
                tt, uu, dd = top[j], up[j], down[j]
                if tt <= 0:
                    j = dd  # spacer: jump to start of next row
                elif colors[j] is not PURIFIED:
                    lengths[tt] += 1
                    down[uu] = up[dd] = j
                j -= 1

        def commit_item(item: int, item_top: int) -> None:
            """Process one item node when its row is added to the partial solution.

            Dispatch based on whether this is a plain primary item or a colored
            secondary item:
              - No color (None): decrement bound; full-cover item if bound hits 0.
              - Color (str): enforce color consistency via tweak.
              - PURIFIED: already committed by a previous tweak; nothing to do.
            """
            assert item_top == top[item]
            color = colors[item]
            if color is None:
                bound[item_top] -= 1
                if bound[item_top] == 0:
                    cover_full(item_top)
            elif isinstance(color, str):
                tweak(item, color, item_top)

        def uncommit_item(item: int, item_top: int) -> None:
            """Reverse of commit_item."""
            assert item_top == top[item]
            color = colors[item]
            if color is None:
                if bound[item_top] == 0:
                    uncover_full(item_top, react=True)
                bound[item_top] += 1
            elif isinstance(color, str):
                untweak(item, color, item_top)

        def tweak(p: int, color: str, top_item: int) -> None:
            """Enforce color consistency for secondary item top_item when row p is chosen.

            We just committed to color `color` for secondary item `top_item`.
            Walk top_item's entire column and:
              - rows whose color differs from `color`: hide them (incompatible).
              - rows whose color matches `color`: mark as PURIFIED (they're compatible
                and no further action is needed when they are later chosen).

            Node p (the row we just selected) is skipped — it retains its original
            color string so that uncommit_item can detect it must call untweak later.
            """
            assert color == colors[p] and color is not None
            q = down[top_item]
            while q != top_item:
                if q != p:
                    if colors[q] != color:
                        hide(q)
                    else:
                        colors[q] = PURIFIED
                q = down[q]

        def untweak(p: int, color: str, top_item: int) -> None:
            """Exact reverse of tweak — restores PURIFIED nodes and unhides hidden rows."""
            assert color == colors[p] and color is not None
            q = up[top_item]
            while q != top_item:
                if q != p:
                    if colors[q] is PURIFIED:
                        colors[q] = color
                    else:
                        unhide(q)
                q = up[q]

        def choose_item() -> tuple[int, bool]:
            """Algorithm M item selection (MRV heuristic) with non-sharp preference.

            For each active primary item c, compute:
                θc = (LEN(c) + 1) monus (BOUND(c) monus SLACK(c))
            where "x monus y" = max(x - y, 0).

            Interpretation of θc:
              - BOUND(c) monus SLACK(c) = max(bound[c] - slack[c], 0) is the number of
                additional rows we must still select to satisfy c's lower bound, taking
                into account that some of the slack may absorb extra selections.
              - LEN(c) + 1 is the number of rows still available for c (including the
                one we are about to try).
              - θc = 0 means it is impossible to satisfy c: not enough rows remain.

            We choose the item with the smallest θc (fewest viable rows — MRV).
            Ties broken by: smaller slack first (tighter constraints first), then
            larger LEN (more options = less likely to cause unnecessary pruning).

            Items whose names start with '#' are deferred: they are only chosen when
            θ ≤ 1 (infeasible or forced) or every remaining item is a sharp item
            with θ > 1.

            Returns (item, feasible) where feasible is False when the minimum θ is 0
            (i.e., there is no valid way to complete the solution).
            """
            best = -1
            best_theta = float('inf')
            best_slack_val = float('inf')
            best_len_val = -1
            preferred = -1      # best non-sharp, or sharp with theta <= 1
            preferred_theta = float('inf')
            preferred_slack_val = float('inf')
            preferred_len_val = -1
            c = right[0]
            while c != 0:
                lam = max(lengths[c] + 1 - max(bound[c] - slack[c], 0), 0)
                if (lam < best_theta
                        or (lam == best_theta and slack[c] < best_slack_val)
                        or (lam == best_theta and slack[c] == best_slack_val
                            and lengths[c] > best_len_val)):
                    best = c
                    best_theta = lam
                    best_slack_val = slack[c]
                    best_len_val = lengths[c]
                if lam <= 1 or not constraint_names[c].startswith('#'): # noqa
                    if (lam < preferred_theta
                            or (lam == preferred_theta and slack[c] < preferred_slack_val)
                            or (lam == preferred_theta and slack[c] == preferred_slack_val
                                and lengths[c] > preferred_len_val)):
                        preferred = c
                        preferred_theta = lam
                        preferred_slack_val = slack[c]
                        preferred_len_val = lengths[c]
                c = right[c]
            if preferred != -1:
                return preferred, preferred_theta > 0
            return best, best_theta > 0

        return search_iterative()

    def create_data_structure(self) -> DLData:
        """Build the DLX data structure, extending the base structure with bound/slack.

        Algorithm M represents each primary item i with two extra arrays:
          bound[i] = hi[i]        — counts down from hi as rows covering i are selected
          slack[i] = hi[i] - lo[i] — how many extra coverages beyond lo are allowed

        Items are removed from the active primary list only when bound[i] reaches 0
        (the upper bound hi is exhausted).  The null-move mechanism handles items
        whose lower bound is met before their upper bound: when all options for an
        active item have been tried and bound[i] <= slack[i] (lo rows already
        selected), the search makes a null move — it skips the item for this level
        without selecting any option — allowing the remaining search to proceed.

        Items defaulting to (lo=1, hi=1) have slack=0, so bound goes 1→0 on first
        cover, which simultaneously removes the item from the active list and hides
        its remaining rows — exactly Algorithm X behavior.
        """
        # Items with bounds (0, 0) mean "this item must never be covered".
        # The simplest way to enforce that is to drop every row that mentions such
        # an item before building the data structure, so those rows are never
        # reachable during search.
        forbidden = {name for name, (lo, hi) in self.bounds.items() if lo == 0 and hi == 0}
        if forbidden:
            constraints = {
                row: items for row, items in self.constraints.items()
                if not any(
                    (c[0] if isinstance(c, tuple) else c) in forbidden
                    for c in items
                )
            }
        else:
            constraints = self.constraints

        data = self._build_dl_data(
            constraints,
            optional_constraints=self.optional_constraints,
            debug=self.debug,
        )

        # Default: every primary item must be covered exactly once.
        # Secondary items (indices primary_length+1..total_length) are never
        # covered in the Algorithm M sense — they are handled by colors — so
        # their bound/slack values are irrelevant and left at the defaults.
        bound_arr = [1] * (data.total_length + 2)
        slack_arr = [0] * (data.total_length + 2)

        for item_name, (lo, hi) in self.bounds.items():
            if lo == 0 and hi == 0:
                continue  # rows were already removed above; item absent from structure
            if lo < 0 or hi < lo:
                raise ValueError(f"Invalid bounds for {item_name!r}: {(lo, hi)}")
            node_index = data.names_map.get(item_name)
            if node_index is None:
                raise ValueError(f"Bounds specified for unknown constraint {item_name!r}")
            elif node_index > data.primary_length:
                raise ValueError(f"Bounds specified for non-primary constraint {item_name!r}")
            bound_arr[node_index] = hi
            slack_arr[node_index] = hi - lo

        data.bound = bound_arr
        data.slack = slack_arr
        return data
