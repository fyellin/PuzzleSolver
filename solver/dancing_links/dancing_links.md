# Dancing Links — Session Context Dump

*Written 2026-04-17 as a reference for future sessions.*

---

## Package layout

```
solver/dancing_links/
    __init__.py
    dancing_links_common.py   — DancingLinksBase, DLData, helpers
    dancing_links.py          — DancingLinks  (Algorithm X + colors)
    dancing_links_bounds.py   — DancingLinksBounds  (Algorithm M)
    orderer.py
```

---

## Classes

### `DLData` (dataclass, `dancing_links_common.py`)

Shared linked-list data structure.  All arrays are plain Python lists indexed by node number.

| Field | Purpose |
|---|---|
| `left`, `right` | Doubly-linked ring of active primary-item headers (root = 0) |
| `up`, `down` | Per-column circular lists (header at top, data nodes below) |
| `top[i]` | Column-header index for data node i; 0 for spacer nodes |
| `lengths[i]` | Number of visible rows in column i |
| `colors[i]` | `None` (primary), `str` (colored secondary), or `PURIFIED` sentinel |
| `constraint_names` | Name string for each header index 1..total\_length |
| `row_names` | `{spacer_node_index: row_name}` |
| `names_map` | `{name: index}` reverse lookup |
| `primary_length` | Count of primary items (indices 1..primary\_length) |
| `total_length` | primary + secondary |
| `bound[i]` | Counts down from `hi` as rows covering item i are selected *(DancingLinksBounds only)* |
| `slack[i]` | `hi - lo`  *(DancingLinksBounds only)* |

`PURIFIED` is a singleton sentinel (`_Purified` class) meaning "color already committed for this node".

### `DancingLinksBase` (ABC, `dancing_links_common.py`)

Shared infrastructure: data-structure builder (`_build_dl_data`), debug printing, `solve()`, `get_name()`.

`solve()` deep-copies `DLData` before the search (in pytest runs) and asserts it is unchanged after — a correctness invariant check.

### `DancingLinks` (`dancing_links.py`)

Algorithm X + optional coloring (Algorithm C).  All items are exact-cover (covered exactly once).  `#`-prefixed constraint names are "non-sharp" and deferred by `choose_column()` unless they are forced (length ≤ 1) or infeasible (length 0).

### `DancingLinksBounds` (`dancing_links_bounds.py`)

Algorithm M: primary items with multiplicity bounds `(lo, hi)`, secondary items with colors.

Key constructor argument: `bounds: dict[str, tuple[int, int]]`.  Items absent from `bounds` default to `(1, 1)`.  Items with `(0, 0)` are forbidden — their rows are dropped before the data structure is built.

---

## Algorithm M mechanics

### Data structure initialisation

`create_data_structure()` builds the shared DLX structure, then appends:

```python
bound[i] = hi[i]
slack[i] = hi[i] - lo[i]
```

Items with `(lo=1, hi=1)` get `slack=0`, reducing to exact Algorithm X behavior.

### Level entry

When `choose_item()` picks `chosen_item`:

```python
bound[chosen_item] -= 1
if bound[chosen_item] == 0 and slack[chosen_item] == 0:
    cover_full(chosen_item)   # full-cover mode: ft = 0
    ft = 0
else:
    ft = down[chosen_item]    # tweaking mode: ft = first option
    if bound[chosen_item] == 0:
        cover_full(chosen_item)   # upper bound hit; hide remaining rows
```

### Full-cover mode (`ft == 0`)

Exactly like Algorithm X: `cover_full` removes the item from the active list and hides every row in its column.  Options are tried via stable `down` pointers (restored before each advance by `uncover_row`).

### Tweaking mode (`ft != 0`)

The item stays active (or leaves only because bound hit 0).  Options are tried by splicing each chosen row out of the item's column via `cover_row`; `uncommit_row` undoes the commits but leaves the splice in place (preventing re-selection at a deeper level).  `restore_tweaked` walks `ft → stop` to unsplice all tried options at backtrack time.

### Null move

When all options are exhausted in tweaking mode and `bound[chosen_item] <= slack[chosen_item]` (lower bound already met), the search tries a null move: skip this item at this level without selecting any row.

If `bound != 0` (cover_full was not called at entry), the null-move hides all tried rows from other items' columns and temporarily removes `chosen_item` from the active list, then falls through to the next `choose_item` call.  The frame encodes `ft` as `-ft` to distinguish it from ordinary frames.

On null-move return, `restore_tweaked` is called, hidden rows are unhidden, and `chosen_item` is re-added to the active list if necessary.

### Stack frame layout

```
[depth, r, chosen_item, ft, index]
```

- `r = chosen_item` at level-entry and null-move frames (sentinel meaning "no row tried yet")
- `ft = 0`: full-cover mode
- `ft > 0`: tweaking mode (value = `down[chosen_item]` at entry)
- `ft < 0`: null-move frame (value = `-ft_original`)
- `index`: 1-based count of options tried so far (for debug output)

Solution extraction: `s[1] > total_length + 1` (filters out header-sentinel frames).

### `choose_item()` — MRV heuristic

For each active primary item `c` compute:

```
θ(c) = max(lengths[c] + 1 − max(bound[c] − slack[c], 0), 0)
```

Interpretation: number of viable rows remaining (0 = infeasible).  Choose the item with the smallest θ.  Ties broken by: smaller slack first, then larger length.

`#`-prefixed items are deferred unless θ ≤ 1 or every remaining item is `#`-prefixed with θ > 1.

---

## Key helper functions

| Function | What it does |
|---|---|
| `cover_row(r, chosen_item)` | Splice r out of chosen_item's column; commit all other items in r's row; mark r's node PURIFIED |
| `uncover_row(r, chosen_item)` | Exact reverse of cover_row (uncommit then restore splice) |
| `uncommit_row(r, chosen_item)` | Uncommit items in r's row without restoring the splice (tweaking advance) |
| `restore_tweaked(chosen_item, ft)` | Unsplice all tried rows back into chosen_item's column, clear PURIFIED marks |
| `cover_full(item)` | Remove item from active list; hide every row in its column |
| `uncover_full(item, react)` | Reverse of cover_full; `react=False` when caller handles re-activation |
| `commit_item(j, top)` | Decrement bound (primary) or call tweak (colored secondary) |
| `uncommit_item(j, top)` | Reverse of commit_item |
| `tweak(p, color, top_item)` | Walk top_item's column; hide incompatible-color rows, mark same-color rows PURIFIED |
| `untweak(p, color, top_item)` | Reverse of tweak |
| `hide(row)` | Splice row out of every column (except chosen_item's) |
| `unhide(row)` | Exact reverse of hide |

---

## Debug output format (`plan.md`)

The plan document specifies the intended debug output once it is fully implemented.

Variables used at print time (after level entry decremented `bound`):

```python
hi = bound[chosen_item] + 1      # pre-decrement hi
lo = max(0, bound[chosen_item] - slack[chosen_item])  # required remaining coverages
```

Append `[lo..hi]` to the item name unless `slack == 0` and `bound == 1`.

**Case 1 (full-cover, `ft == 0`):** Standard Algorithm X display.  `N = lengths + index` (pre-decrement).  Forced (N=1): bullet prefix `"• "`.  Branch (N>1): `"k/N "` prefix.  Infeasible (N=0): handled by `_print_infeasible`.

**Case 2 (tweaking, must-cover, `bound > slack`):** `lo_eff = bound - slack`.  Viable choices = `N - lo_eff + 1`.  Forced if choices = 1, branching if > 1, infeasible if ≤ 0.

**Case 3 (tweaking, optional, `bound <= slack`):** N+1 total options (N rows + null-move).  Null-move is the last branch and is printed by a separate `_print_null_move` call when the null-move frame is pushed.

**Depth rule:** `depth += (n_rows > 1)` — depth only increases when there is a genuine branch.

---

## Deferred work (from prior sessions)

### 1. `FT[]` in `tweak` / `untweak` (performance)

Knuth's Algorithm M stores `FT[l]` (first-tweaked pointer at level l) so that `untweak` only needs to walk back to that point rather than the entire column.  The current `untweak` walks the whole column every time.  This is a **correctness-neutral performance optimization**.

Fix: store one extra value per stack frame (or a parallel list); rewrite `tweak`/`untweak` to fill/consume it.  Difficulty: **moderate, localized**.

### 2. `seen_solutions` / extra-items phase (design)

There is no `seen_solutions` deduplication in the current code (it was a prior design that was removed).  The current null-move mechanism achieves correct enumeration without it.

If this topic comes up again, verify against the live code before assuming the old analysis still applies.

---

## Tests

Tests live under `tests/` (pytest, plain `assert`).  Key tests for bounds behavior:

- `test_slack_optional_cover` — expects `{r1, r2}` for A(1,2), B(1,1), r1:[A,B], r2:[A]
- `test_slack_zero_to_two` — expects `{r1,r3}` and `{r2,r3}` for A(0,2), B(1,1)
- `test_all_optional_primary_items` — marked `xfail`