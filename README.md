# MagpieSolver

A Python framework for solving numeric crossword puzzles — particularly Magpie and Listener puzzle variants where clue answers are numbers derived from equations or constrained by mathematical properties.

## Solver types at a glance

| Solver | Use when |
|---|---|
| `EquationSolver` | Each clue is an algebraic expression in letter variables (e.g. `A+B*C`) |
| `ConstraintSolver` | Each clue is independently generated (prime, square, …) and linked by relationships |
| `DancingLinksSolver` | Complex set-cover problems; Algorithm X with colored constraints |

All three inherit from `BaseSolver`, which handles grid management, symmetry checks, and plotting.

---

## Key terms

### Location

A location is a specific square in the grid, represented as `(row, col)` with `(1, 1)` at the top-left corner. For example, `(4, 1)` is the first column of the fourth row.

The framework only handles rectangular grids, but since clues are not required to occupy consecutive locations, you can work around this. For example, Listener 4569 is a 4×4×4 cube modeled as a 16×4 rectangle.

### Clue

The basic unit of a puzzle. Key attributes:

| Attribute | Description |
|---|---|
| `name` | Identifier, e.g. `"1a"`, `"3d"` |
| `is_across` | `True` for across, `False` for down |
| `base_location` | `(row, col)` of the first cell |
| `length` | Number of cells (digits) |
| `locations` | Ordered sequence of all `(row, col)` cells |
| `location_set` | Frozenset of cells, for quick intersection tests |
| `expression` | Equation string for `EquationSolver` |
| `evaluators` | Compiled evaluators derived from `expression` |
| `generator` | Callable `(clue) -> Iterable` for `ConstraintSolver` |
| `context` | Any puzzle-specific payload; `Clue` is generic (`Clue[T]`) |

Constructor signature:

```python
Clue(name, is_across, base_location, length, *,
     expression='', generator=None, context=None,
     locations=None, priority=0)
```

#### Expressions and evaluators

An expression is a string with letter variables. The parser understands implicit multiplication (`2AB(C+D)` → `2*A*B*(C+D)`), standard arithmetic (`+`, `-`, `*`, `/`, `^`/`**`), functions `sqrt()` and `fact()`, everything in `math`, and the typesetter characters `−`, `×`, `√`.

Each expression compiles to one or more `Evaluator` objects stored in `clue.evaluators`. Multiple evaluators arise when the expression contains `=` signs. An evaluator's free variables are in `evaluator.vars`. Calling `evaluator(value_dict)` yields positive integer strings, or nothing if the result is not a valid positive integer.

#### Generators

A generator is a callable `(clue: Clue) -> Iterable[int | str]` that produces the candidate values for a clue. It is called once per clue; efficiency matters only at scale. The `solver.generators` module provides ready-made generators (see below). A generator of `None` means the solver ignores that clue entirely (rare; useful when only intersecting clues can determine its value).

#### Non-standard clue paths

Pass `locations=` to specify exact cell paths for non-rectangular grids:

```python
clue = Clue("1a", True, (1, 1), 5, locations=[(1,1), (2,3), (4,5), (1,7), (3,9)])
```

When `locations` is given, `base_location` and `length` in the constructor are ignored; the clue derives them from the list. `is_across` is stored but has no effect on cell layout.

---

## Defining the grid

### `Clues.clues_from_clue_sizes(across, down)`

The most concise format. One string per direction; each row/column is a token where each digit is the length of one clue and `1` is an unchecked cell.

```python
ACROSS = "23/32/23"   # row 1: 2-digit clue then 3-digit; row 2: 3 then 2; …
DOWN   = "222/333"    # col 1: two 2-digit clues stacked; col 2: two 3-digit clues; …
clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
```

Clue names are assigned automatically from starting-cell number.

### `Clues.create_from_text(across, down, locations)`

Parses lines in the format `"number  expression  (length)"`. The `locations` argument is either a grid string (`X` = clue cell, `.` = blank) or a sequence of `(row, col)` tuples.

```python
GRID = """
X..X..X
XXXXXXX
X..X..X
"""
ACROSS = """
 1  A+B (2)
 3  C*D (3)
"""
clues = Clues.create_from_text(ACROSS, DOWN, GRID)
```

### `Clues.create_from_text2(across, down, across_lengths, down_lengths)`

Combines the compact length encoding with free-form expression lines (no `(length)` suffix needed). Preferred when expressions are long.

```python
ACROSS_LENGTHS = "232/133/2122"
DOWN_LENGTHS   = "322/421/133"

ACROSS = """
 1  T(W+O)-PR+OP-E+R+BE+A+TS
 3  TOO+LS+S+H+ED+S
"""
clues = Clues.create_from_text2(ACROSS, DOWN, ACROSS_LENGTHS, DOWN_LENGTHS)
```

Pass `create_unmatched_clues=True` to create bare `Clue` objects for any grid cells that have no expression.

---

## EquationSolver

Use this when clue values come from algebraic expressions over shared letter variables.

### Constructor

```python
EquationSolver(clues, items, *, allow_duplicates=False)
```

- `clues`: sequence of `Clue` objects, each with an `expression`
- `items`: iterable of integers to assign to letters (e.g. `range(1, 27)` for A–Z = 1–26)
- `allow_duplicates`: if `True`, multiple letters can share the same value, and multiple clues can share the same answer

### Solving

```python
solver.solve(debug=False, max_debug_depth=2)
```

The solver precomputes an optimal evaluation order (fewest unbound variables first, then most grid intersection coverage, then longest clue) and backtracks recursively. With `debug=True` it prints progress; `max_debug_depth` limits how deep the trace goes.

For large search spaces use `MultiEquationSolver`, which distributes work across CPU cores with the same API.

### Adding constraints

```python
# Single clue
self.add_constraint(('1a',), lambda x: int(x) % 2 == 0)

# Multiple clues — predicate receives one value per clue, in the listed order
self.add_constraint(('1a', '3d'), lambda x, y: int(x) + int(y) == 100)
```

Clues can be identified by name string or `Clue` object. Constraints are checked as soon as all listed clues have values.

### Overridable callbacks

```python
def check_solution(self, known_clues: KnownClueDict,
                   known_letters: KnownLetterDict) -> bool:
    # Return False to reject this candidate solution
    return True

def show_solution(self, known_clues: KnownClueDict,
                  known_letters: KnownLetterDict, **kwargs) -> None:
    super().show_solution(known_clues, known_letters, subtext="Hidden message")

def get_letter_values(self, ...):
    # Override when the assignment rule is more complex than
    # "each letter gets a distinct value from items"
    ...
```

`known_clues` maps each `Clue` to its digit string; `known_letters` maps each variable letter to its integer.

### How it works

1. Precompute evaluation order: rank evaluators by (a) fewest unbound letters, (b) most intersections with already-chosen clues, (c) longest clue.
2. Recursively assign values. For each evaluator in order:
   a. Call `get_letter_values()` to enumerate permutations of still-unassigned variables.
   b. Evaluate the expression; skip if result is not a positive integer of the right length.
   c. Check that the value matches already-filled grid cells at intersections.
   d. Skip if value is already used and duplicates are not allowed.
   e. Check all constraints whose clues are now fully known.
   f. Recurse.
3. When all evaluators are assigned, call `check_solution()`, then `show_solution()`.

---

## ConstraintSolver

Use this when clues are generated independently and linked by relationships. No shared letter variables.

### Constructor

```python
ConstraintSolver(clues, *, allow_duplicates=False)
```

### Setup pattern

```python
from solver import Clues, ConstraintSolver, generators

class MyPuzzle(ConstraintSolver):
    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        for clue in clues:
            clue.generator = generators.prime
        super().__init__(list(clues))
        self.add_constraint(('1a', '3d'), lambda x, y: int(y) % int(x) == 0)
```

### Generators (`solver.generators`)

All generators have signature `generator(clue: Clue) -> Iterable[int | str]` and automatically produce values of the right digit count.

| Generator | Returns |
|---|---|
| `allvalues` | All integers that fit the clue length |
| `prime` | Primes |
| `not_prime` | Composites |
| `square` | Perfect squares |
| `cube` | Perfect cubes |
| `nth_power(n)` | n-th powers (returns a generator factory) |
| `triangular` | Triangular numbers |
| `fibonacci` | Fibonacci numbers |
| `lucas` | Lucas numbers |
| `palindrome` | Palindromic numbers |
| `sum_of_2_cubes` | Sums of two positive cubes |
| `permutation(alphabet)` | Non-repeating digit permutations |
| `known(*values)` | A fixed set of values |
| `filterer(predicate)` | All values satisfying `predicate(value)` |

### Constraint API

```python
# Standard: predicate must return True; checked when all but one listed clue is known
self.add_constraint(('1a', '3d'), lambda x, y: int(x) < int(y))
self.add_constraint(('1a',), lambda x: int(x) % 2 == 0)   # single-clue ok here too

# Extended: can also prune candidates for the first still-unknown clue
# Signature: predicate(current_candidates, v1, v2, ...) -> filtered_candidates
# vi is None if that clue is not yet assigned
self.add_extended_constraint(('3d', '1a', '6a'), my_trimmer)

# Space-separated name string is also accepted
self.add_extended_constraint("3d 1a 6a", my_trimmer)
```

Extended constraints receive the current candidate list for the first unknown clue and `None` for clues not yet solved. They return a (possibly filtered) candidate list.

### Helper predicates (`solver.helpers`)

```python
from solver.helpers import is_square, is_cube, is_triangular, is_fibonacci
from solver.helpers import digit_sum, digit_product, is_harshad
from solver.helpers import extended_multiply_constraint, extended_add_constraint
```

`extended_multiply_constraint` and `extended_add_constraint` are ready-made extended constraints for three clues where one is the product (or sum/difference) of the other two, regardless of which is not yet known:

```python
# 3d = 1a × 6a, whichever direction is being computed
self.add_extended_constraint("3d 1a 6a", extended_multiply_constraint)
```

### Advanced: generator of `None`

Rarely, a clue is fully determined by its intersecting clues. Assign `generator=None` and let `check_solution()` verify the value that the intersections filled in.

### Advanced: subclassing `str`

When a clue value carries metadata beyond its digit string (e.g. tracking how it was generated), subclass `AbstractClueValue`:

```python
from solver import AbstractClueValue

class MyValue(AbstractClueValue):
    def __new__(cls, value: str, tag: str):
        obj = super().__new__(cls, value)
        obj.tag = tag
        return obj
```

Generators return `MyValue` instances; constraints and `check_solution` receive them.

### How it works

For each clue, the generator produces all candidate values, filtered by `get_allowed_regexp()` (no leading zeros, etc.). Then a recursive search runs:

1. Pick the clue with the fewest remaining candidates (tie-break: longest length).
2. If it has zero candidates, backtrack.
3. For each candidate value:
   a. Apply all constraints that now have exactly one unknown clue; prune that clue's candidates.
   b. Remove values from other clues that clash at grid intersections.
   c. Recurse.
4. When all clues are assigned, call `check_solution()`, then `show_solution()`.

---

## DancingLinksSolver

Uses Algorithm X (Dancing Links) for exact-cover problems. Suitable when clue values must collectively satisfy mutually exclusive or colored constraints.

### Setup pattern

```python
from solver import Clues, DancingLinksSolver

class MyPuzzle(DancingLinksSolver):
    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        for clue in clues:
            clue.generator = my_generator
        super().__init__(clues)
```

### Extension points

```python
def update_constraints(self, constraints, optional_constraints, bounds):
    # Inject additional rows or columns into the DL matrix before solving
    pass

def get_clue_value_constraints(self, clue, value, optional_constraints):
    # Return extra DL column entries for this (clue, value) pair
    return list(super().get_clue_value_constraints(clue, value, optional_constraints))

def check_raw_solution(self, solution) -> bool:
    # Early prune before multi-clue constraint checks
    return True
```

---

## BaseSolver utilities (all solvers)

```python
# Look up a clue by name
clue = self.clue_named("1a")

# Verify grid symmetry (call during __init__ after building the grid)
self.verify_is_180_symmetric()
self.verify_is_four_fold_symmetric()
self.verify_is_vertically_symmetric()

# Restrict which digit characters are allowed in a given cell
def get_allowed_regexp(self, location: Location) -> str:
    return "[1-9]"   # default: no leading zeros; override for tighter restrictions

# Draw the empty board (useful during development to check grid shape)
self.plot_board({})
```

It is strongly recommended to verify grid symmetry and plot the empty board before running the solver. Mistakes in the grid description are easy to make and hard to debug otherwise.

---

## Visualization

Override `draw_grid` to customize the solved grid display:

```python
from typing import Unpack
from solver import DrawGridKwargs

def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
    super().draw_grid(
        blacken_unused=False,
        shading={(2, 3): 'lightblue'},
        subtext="Hidden message",
        **args
    )
```

Key keyword arguments (all optional):

| Argument | Effect |
|---|---|
| `blacken_unused` | Fill unused cells solid black (default `True`) |
| `shading` | `{location: color}` for cell background colors |
| `coloring` | `{location: color}` for digit text colors |
| `circles` | Set of locations to circle |
| `subtext` | String displayed below the grid |
| `top_bars` / `left_bars` | Sets of locations where thick bars appear |
| `extra` | Callable for additional matplotlib drawing |

---

## Type reference

```python
from solver import Location, Letter, ClueValue, AbstractClueValue
from solver import KnownClueDict, KnownLetterDict

Location        = tuple[int, int]       # (row, col), 1-indexed
Letter          = str                   # single variable letter
KnownClueDict   = dict[Clue, ClueValue]
KnownLetterDict = dict[Letter, int]
```

`ClueValue` is a protocol satisfied by strings and integers that support `str()`, `int()`, `len()`, and indexing. Subclass `AbstractClueValue` to build richer value types.

---

## Quick-start templates

### EquationSolver

```python
from solver import Clue, Clues, EquationSolver, KnownClueDict, KnownLetterDict

ACROSS_LENGTHS = "23/32/23"
DOWN_LENGTHS   = "222/333"

ACROSS = """
 1  A+B
 3  C*D
"""
DOWN = """
 2  B+C
 4  D-A
"""

class MyPuzzle(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False)

    def __init__(self):
        clues = Clues.create_from_text2(ACROSS, DOWN, ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues, items=range(1, 10))

    def show_solution(self, known_clues: KnownClueDict,
                      known_letters: KnownLetterDict) -> None:
        super().show_solution(known_clues, known_letters)

if __name__ == '__main__':
    MyPuzzle.run()
```

### ConstraintSolver

```python
from solver import Clues, ConstraintSolver, generators
from solver.helpers import extended_multiply_constraint

ACROSS = "23/32/23"
DOWN   = "222/333"

class MyPuzzle(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False)

    def __init__(self):
        clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        for clue in clues:
            clue.generator = generators.prime
        super().__init__(list(clues))
        self.add_constraint(('1a', '3d'), lambda x, y: int(y) % int(x) == 0)
        self.add_extended_constraint("1a 3d 5a", extended_multiply_constraint)

if __name__ == '__main__':
    MyPuzzle.run()
```

---

## Solved puzzle notes

### EquationSolver puzzles

**Listener 4569** — Grid is a 4×4×4 cube modeled as a 16×4 rectangle. Custom `locations=` arguments route clues through the correct cells. `draw_grid` is overridden to suppress the normal thick bars and insert horizontal dividers between layers. A second call replaces digits with the hidden word's letters.

**Listener 4922** — Variables are perfect squares (2²–50²). Clues are grouped in sets of four; the sum of each group's values must also be a perfect square.

**Magpie 269** — Uses `allow_duplicates=True` with values 1–99. The "grid" is a flat list of letter-pair clues; `get_allowed_regexp` returns `".*"` to allow any value. Clue positions are virtual; the real information is in the ordering constraints between groups.

**Magpie 281** — Each clue expression has one letter removed; both the remaining expression and the removed letter must be determined simultaneously. Uses a custom evaluator wrapper that tries all possible letter deletions and records which deletion yields the correct answer.

### ConstraintSolver puzzles

**Listener 4542** — Clue generators enumerate numbers that match both a clue's digit length and the expected length of the English spelling of the answer. Evaluators are repurposed as constraints by matching their free variable names to clue names.

**Listener 4555** — One of the few uses of `generator=None`. D7 is a 7-digit non-prime; enumerating several million candidates is impractical, so the solver lets intersecting clues fill it in and `check_solution()` verifies the result.

**Listener 4908** — Symmetric grid (left/right mirror). Each pair of mirrored clues draws from complementary number sets. An extended bitmap constraint enforces that no digit appears twice within the same half.

**Magpie 200** — Subclasses `str` to attach generation metadata to each value. Every clue has a constraint against every other clue to enforce uniqueness of the metadata.

**Magpie 202** — Puzzle is in hexadecimal. All generators produce strings (not integers, which would be stringified in base 10). `draw_grid` is overridden to substitute letters and apply rotation/shading.
