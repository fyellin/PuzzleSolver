# Puzzle Solver.

This directory contains code to help you solve generic numeric crossword puzzles.  It is designed to solve two different sorts of numeric crossword puzzles:

* `EquationSolver`: Puzzles where each clue has an equation with letters as the variables.  Users must find the correct assignment of a number to each letter so that the grid can be filled.

* `ConstraintSolver`: Each clue has constraints on the answers that can go into that spot.  In some cases, answers suitable for one clue further restrict the answers that are suitable for other clues,

## Key concepts

### Location

A location is a specific square in the grid.
Locations are represented by a tuple of two small integers representing
the row and column, respectively, with `(1, 1)` being the top left corner.
For example `(4, 1)` refers to the first column of the fourth row.

The program can only handle rectangular grids. 
However, since there is no requirement that a clue occupy
consecutive location, this can usually be kludged around.
For example, this program has been used to solve a 4x4x4 grid by pretending the layers are vertically stacked on each othe as a 16x4 grid.

### Clue

The basic unit of a puzzle is the `Clue`.  Each clue has the following attributes:

* `name`: for identification purposes only
* `base_location`: the location of the first letter of the clue
* `is_across`: true if this is an across clue, false if this is a down clue
* `length`: the number of squares of this clue
* `expression`: for `EquationSolver` puzzles, the expression giving the value of this clue.  This field can also be used by `ConstraintSolver` puzzles, too, but its use in then up to the user.
* `generator`: for `ConstraintSolver` puzzles, a generator that generates all legal values for this clue.


#### The Expression
The expression is a string representing an equation with variables, where the variables are the
upper- and lower-case letters.  This is converted into a Python expression and compiled.  The conversion process understands implied multiplication (i.e. `2ab(c+d)` means `2*a*b*(c+d)`); it also understands the strange subtraction symbol used by Listener and Magpie.

To evaluate a clue's expression, call `clue.eval(dictionary)`, where the `dictionary` argument is a mapping from variables to the integer value of those variable.  If the result is a positive integer, it is returned as a string. `None` is returned if the result is negative or non-integer.  

NOTE: We do not yet handle the expression throwing an error.  Should this be fixed?


#### The Generator
The generator is a function that takes a `Clue` argument (mainly for its length) and returns possible clue values.  
The returned clue values can either be an integers or a string.  The generator returns either an iterator, a list, or a generator of such values.  

In very rare cases, the generator can be `None`.  This is described later.

The file `Generators.py` contains several generators of the sort that are frequently found in Magpie puzzles.  It also contains generators that return a pre-calculated list and generators that just return every possible value.  The latter probably shouldn't be used for clues longer than length 6.


#### Non-standard clues and subclassing
   
If your grid is not actually a rectangle, you may need to subclass `Clue`.  

The code assumes that across clues start at the indicated location and move right (increasing the second index),  and that down clues start at the indicated location and move down (increasing the first index). 
If your puzzle has different rules, you should subclass `Clue` and override the method `generate_location_list` to generate the list of locations.

TODO: Verify length?  Verify first element is base_location? 

#### Twinning

In some `EquationSolver` puzzles, there are clues whose equation contains an equal sign.
For example: `ACROSS 5. A + B = CDD (3)`.  Rather than treating this as an equation with four 
distinct variables, it is typically faster to pretend that there are two different clues, both labelled `5`, each containing two distinct variables.  We consider these two separate clues to be "twins" of each other.

Twins create some complications.  

* In many puzzles, there is the restriction that that no two clues have the same answer; yet obviously twins are 
supposed to have the same answer as each other.  

* Likewise, some puzzles place limitations on what letters may go into an intersection.  Yet every square of a clue 
intersects with the same square of its twin.  When twinning occurs, we must be very precise whether we are including
a twin intersecting with its other half, or not.


### Clue list

A `ClueList` gathers together a set of clues and creates information them as a set.  

For the `EquationSolver`, there is a convenience function that lets you copy and paste the equations from the puzzle and directly generate a clue list.  

    clue_list = ClueList(sequence_of_clues)
    
#### Subclassing ClueList
    
There are a few reasons to subclass `ClueList`:

* In most puzzles, the first digit of an answer cannot be zero.  In some puzzles, there may be further restrictions.
* The user can override `is_zero_allowed(location)` if there are alternative restrictions.
The default implementation returns `True` when the location is not the starting location of any clue.

* Some puzzles may have other restrictions on digits.
The user can override `get_allowed_regexp(location)` to indicate the allowable values. 
The default implementation calls `is_zero_allowed(location)` above and returns
either `"."` or `"[^0]"` on a `true` or `false` result, respectively.
Any appropriate regexp that matches at most a single character is allowed.

* `ClueList` is responsible for printing the grid once a solution has been found.
The default implementation of `draw_grid` just calls the `DrawGrid` utility with the arguments it has been passed.
By overriding this method, the user can intervene and modify the arguments before calling `super().draw_grid(...)`.

Among some examples for overriding `draw_grid` are:

* Replacing the digits in the result with the letters of a key word
* Adding shading to the grid
* Changing the location of thick bars.

#### Verification of the grid.

`ClueList` contains three very important verication functions:

* `clue_list.verify_is_180_symmetric`: The grid should look the same if it is rotated 180°.  The method throws an assertion error if that is not the case.

* `clue_list.verify_is_four_fold_symmetric`: The grid should look the same if it is rotated either 90° or 180°.  The method throws an assertion error if that is not the case.

* `clue_list.verify_is_vertically_symmetric`: The grid should look the same in a mirror as it does normally.

When first creating a grid, it is highly recommended that you write:

    clue_list = ....
    clue_list.plot_board({})
    clue_list.verify_is_180_symmetric() # or whichever symmetry is appropraite
    
It is extremely easy to make a mistake when describing the grid.
Asking Python to show you a picture of the empty 
board and to verify that it has the symmetry you expect will save you a lot of grief.


## Solving crossword puzzles

### The equation solver

The `EquationSolver` is by far the simplest of the two.
A typical call to create an equation solver looks like the following:

    EquationSolver(clue_list, items=list(range(1, 27)))

The arguments indicate:

* The clue list for the puzzle, 

* The allowable values for the variables are 1..26 inclusive, and each value can be used at most once.  
\[Note, the values in the list must be distinct.  See below if variable values can be repeated.]

* Typically, each equation must yield a distint value.  If duplicate values are allowed, then add the keyword argument `allow_duplicates=True` to the argument list.

There are three methods you may want to override:

* `check_solution()` is called when the solver has found a tentative solution.
The default implementation simply returns `True`, but additional puzzle-specific verification can be performed hear.

* `show_solution()` is called after `check_solution()` returns `True`.  It prints out the values of the variables and draws a picture of the grid.  Users can augment or replace this behaviour.

* `get_letter_values()` is called to find all possible values to assign to letters, given previously existing  assignments.  You must override this if the puzzle uses something more complicated than each variable must get a distinct value from the list passed as the `item=` argument. See Magpie195 for an example.

The solver is run by calling `solver.run()`.  More information about the steps the solver is performing can
be seen by adding the arguemnt `debug=True`.

    
#### How it works.

This solver first determines the order in which to solve the clues.  It repeatedly ranks the clues based on the following criteria:

1. Which clue has the fewest number of letters not yet assigned a value.
1. If there is a tie, which of those clues has the largest percentage of squares that intersect with already selected clues.
1. If there is a tie, which is the longest.
1. If there is still a tie, a random one is chosen

After each "best remaining" clue is chosen, each of the remaining clues needs to be re-evaluated for the next round; some of its letters may no longer be unassigned, and some of its squares may have intersected the just chosen clue.

The solver performs a search through the clues in this calculated order.  
As a result, when the solver next looks a clue, it has already precalculated which letters in the clue have already been assigned, which letters still need to have a value assigned to hem, and which letters of its answer have already been filled by previous answers.

Given this order for solving the clues, the solver calls the following recursive algorithm, starting with n = 0

1. If n is the the number of clues, we have a tentative solution.  Call `check_solution()`, and if it returns `True`, call `show_solution()` and return.

1. Find the n-th clue in the order we are solving them, as determined above.
1. Calculate a regular expression that matches legal values for this clue, taking into account 
   -  squares filled by already solved intersecting clues, 
   -  squares that can't contain 0, and 
   - other interesting facts determined by `get_allowed_regexp()`.
1. Call `get_letter_values()` to determine all possible values that this clue's unknown variables can take. For each set of possible values for the variables:
    1. Evaluate the expression using the variables and their values.
    1. If the value of the expression is an illegal result, or if the value
       doesn't match the regular expression, continue.
    1. If the value of the expression is a value we've already used and `not use_duplicates`
       then continue
    1. Add the current variables and values to the set of known value
    1. Recursively run this algorithm with n + 1
    1. Remove the current variables and values from the set of known values


### The Contraint Solver

A typical call to create a `ConstraintSolver is as follows:

    EquationSolver(clue_list, allow_duplicates=False)

The two arguments, respectively, indicate:

* The clue list for the puzzle is the specified clue list, 
* Each clue answer must be a distince value.  \[Note: `False` is the default value for `allow_duplicates`, and this keyword is usually  elided.]

There are three methods you may want to override:

* `check_solution()` is called when the solver has found a solution.  The default implementation simply returns`True`, but additional puzzle-specific verification can be performed hear.
* `show_solution()` is called when `check_solutions()` returns `True`.  It prints out a picture of the grid.
* `post_clue_assignment_fixup()` is called each time a clue is assigned a tentative value.

The method `post_clue_assignment_fixup()` is almost always overridden, and is described later.

The solver is then run by calling `solver.run()`.  More information about the steps the solver is performing can be seen by adding the argument `debug=True`.


### `post_clue_assignment_fixup`

The goal of `post_clue_assignment_fixup` is to add information about a clue that we could not handled when we first
generted the initial possible values for the clue.  This function is passed

* The clue to which we just assigned a value.
* A dictionary of all clue that have been assigned values, and their corresponding values.
* A dictionary of all clues that have not yet been assigned values, and a frozen set of their possible values.
Clues that were given a generator of `None` will not be in either dictionary until they are explicitly added 
in the step below.

The method can do any or all of the following:

* Return `false`, indicating this value should be rejected.
* Replace the value of any of the frozen sets indicating the set of their possibles with a different set.  
  Typically the new set should be a subset of the original set, but this isn't enforced.
* Any clue to which we initially passed `None` as a generator will not be in any dictionary.  This function can
  add a frozen set indicating possible values for that clue to the dictionary of not-yet-assigned values.  \[Even if 
  the value is a singleton, it should be added to the not-yet-assigned values rather than to the assigned values.]
  
There are several methods in `ConstraintSolver` that are useful in writing your `post_clue_assignment_fixup`.

`check_clue_filter` is called when we have a new restriction on the values that a clue can have that we did
not know about originally.  It is passed a clue and a predicate argument.  If we already known the value of the clue,
it returns `true` if the value satisifies the predicate.  If we don't yet know the value of the clue, the set of possible
values for the clue is pruned to include only those values that match the predicate.  It returns `False` if the
pruning yields the empty set the empty set.  See Listener4542 for an example.

`check_2_clue_relationship` can be  called when a relationship between two clues, and one of them has been assigned a value.  So, for example,

    self.check_2_clue_relationship(a1, a2, unknown_clues, lambda x, y; y % x == 0)

makes sure that a2 is a multiple of a1.  Whenever one of them is assigned a value, the other one's values will
be pruned.

### Advanced techniques 

#### Clues with a generator of `None`

It is rare, but legal to give a clue a generator of `None`.  This clue is completely
ignored by the solver until it assigned a set of possible values by `post_clue_assignment_fixup`.

In some rarer cases, it is necessary to delay the value of a clue until `check_solution()`.  For example, if a clue's value is listed as "the sum of all the digits in the puzzle" or "a seven-digit non-prime",  it's probably best to wait until `check_solution()` to see if a reasonable value has been put into the clue by crossing clues.

#### Subclassing `string`

Sometimes, a clue value contains information beyond just its value.  The value must keep track of some particular fact about how it was generated, and this information is not easy to store into a table.  Python allows the user to subclass string.  See XXX for an example of how this is done.

Your generators should produce instances of your string subclass rather than integers or normal strings.  `SolveByLetter` will never produce new clue values on its own.  When `post_clue_assignment_fixup()` and `check_solution()` are called you can be assured that all
clue values, will be your subclass of string, and you can freely treat them as objects of that type.

### How it works

For each clue, the generator is called to calculate the set of all possible answers for that clue.  This list of clues is filtered by taking into account `is_zero_allowed()` and `get_allowed_regexp()` for each location, thereby ensuring that there are no zeros where they aren't allowed.

The following recursive algorithm is then followed.  We have as input a dictionary of clues, and for each clue a set of possible values that the clue can take.

1. If the dictionary is empty, we are done.  Call `check_solution()`, and if that returns `true`, call `show_solution()`. Return.
1. Find the clue that has the smallest number of possible values.  If there is a tie, use the clue that has the longest length.  If there is still a tie, pick one at random.  
1. If the number of possible values for this clue is zero, then return.
1. For each possible value that this clue can take (the "current value"), do the following:
   1. Call `post_clue_assignment_fixup`.  Continue if this returns `false`.
   1. Create a dictionary that is a copy of the current dictionary except:
      * The current clue is removed as a key
      * Unless duplicate entries are allowed, remove the current value from all the other sets
      * If the current clue intersects with another clue, remove all entries that clash at the
        intersection.
   1. Recursively call this function 


# Sample code

## Equation puzzles.

The typical code for an equation puzzle is quite simple!
You create a grid and a list of across and down clues.

    GRID = """
    XX.XXXXX.XX
    .X....X....
    X.XX.X.XX..
    X...X..X..X
    XX.XX.X..X.
    X....X.X...
    X...X..X...
    """

    ACROSS = """
    1 JE(RK + S) (4)
    4 SEAM (3)
    7 CAGE (4)
    10 EXTEND (5)
    ...
    """

    DOWN = """
    1 ERRED (4)
    2 TEETERS (3)
    3 N(O – U)N (2)
    4 TOOT (3)
    ...
    """

    VALUES = list(range(1, 27)) # 1.26 inclusive.

The following code is then all you need to solve this puzzle:

    locations = ClueList.get_locations_from_grid(GRID)
    clue_list ClueList.create_from_text(ACROSS, DOWN, locations)
    solver = EquationSolver(clue_list, VALUES)
    solver.run()().
    
    
# Solved Puzzles

## EquationSolver

### Listener 4569

The grid is a cube, and there are "through" clues as well as clues that go across or down a single layer.  In addition, there are rules about a clue going off the edge of its own layer.  

To solve this, we model the 4x4x4 cube as a 16x4 rectangle, and subclass `Clue` in order to implement the clue rules.  The solution is straightforward

`ClueList` is overridden so that the generated grid appears more pleasing.  We don't want the normal thick bars printed out.  Instead, we just want thick bars as a break between each of the 4x4 layers.  In addition, once we read the hidden message and know the secret ten-letter word, 
we print the grid a second time with letters replacing the digits in the grid.

### Magpie 195
A straightforward set of equations that we could solve just by copy and paste.

### Magpie 197
A straightforward `EquationSolver` with no complications.

## ConstraintSolver

### Listener 4542

Each clue is labelled by a letter.  Each clue has a number and an equation associated with it.  The number gives the number of letters in the English spelling of the clue, and the equation indicates the sum of the distinct letters (A=1, B=2, etc) of the English spelling.

The solver is set up as a `ConstraintSolver`, where the generator lists all numbers that when are the number of digits specified by the clue and then when written out have the indicated number of letters.  

The `post_clue_assignment_fixup` works cleverly.  Each time a clue (and thus a letter) gets a value, it looks through all the equations of all the clues, and finds those equations for which this letter is the unknown.  For each of those equations, it evaluates the value, and then uses `self.check_clue_filter` on the corresponding clue to ensure that only a correct value is in that slot.

### Listener 4555

A `ConstraintSolver` with extraordinarily complicated interplay between the clues.

This is one of the few uses of `generator=None`.  Since the only thing we know about D7 is that it is a 7-digit non-prime, it was easier to just test it after all the other clues were assigned, rather than to enumerate all several million non-primes.

### MagPie 145

Interesting rules for setting up the generators, but a straightforward solve.

### Magpie 146

Actually two puzzles.  The first involves finding out the values of the entries, and the second involves fitting the entries into the grid.  The second puzzle is a straightforward `ConstraintSolver`

More about the first puzzle. . .

### Magpie 153

A complicated ConstraintSolver, with lots of work in the post fixup because lots of clues must be multiples of lots of other clues

### Magpie 196
A straightfoward `ConstraintSolver`, except the generators had to be adjusted for non-base-10

## Other puzzles.

### Magpie 149

One of a kind.  Worth describing?

### Magpie 194
An amazing extremely hard puzzle that didn't fit in with us.  Lots of logic.  

## Magpie 198





`







