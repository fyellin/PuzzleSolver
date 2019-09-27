# Puzzle Solver.

The solver/ directory contains code to help you solve generic numeric crossword puzzles.
It is designed to solve two different sorts of numeric crossword puzzles:

* `EquationSolver`: Puzzles where each clue has an equation with letters as the variables.
The solver must find the correct assignment of a number to each letter so that the grid can be filled.

* `ConstraintSolver`: Each clue has constraints on the answers that can go into that spot, such as "must be prime"
or "must be square".
In some cases, there are further constraints between the answers of clues, so as that one clue divide another.

## Key terms

### Location

A location is a specific square in the grid.
Locations are represented by a tuple of two small integers representing
the row and column, respectively, with `(1, 1)` being the top left corner.
For example `(4, 1)` refers to the first column of the fourth row.

This program can only handle rectangular grids. 
However, since there is no requirement that a clue occupy
consecutive location, this can be kludged around.
For example, we have used this program to solve a 4x4x4 grid by pretending the layers are vertically 
stacked on each other as a 16x4 grid.

### Clue

The basic unit of a puzzle is the `Clue`.
Each clue is created with the following attributes:

* `name`: for identification
* `base_location`: the location of the first letter of the clue
* `is_across`: true if this is an across clue, false if this is a down clue
* `length`: the number of squares of this clue
* `expression`: for `EquationSolver` puzzles, the expression giving the value of this clue.
This field can be used by `ConstraintSolver` puzzles, too, but its use in then up to the user.
* `generator`: for `ConstraintSolver` puzzles, a generator that defines the initial set of
 legal values for this clue.
* `context`: The user can use this to store additional information.

#### The Expression, Evaluators
The expression is a string representing an equation with variables, where the variables are
upper- and lower-case letters.
This is converted into a Python expression and compiled.
The converter understands implied multiplication i.e. `2ab(c+d)` means `2*a*b*(c+d)`;
it also understands the subtraction symbols used by  the typesetters of Listener and Magpie.

Each expression is turned into on or more `Evaluator`s.
Multiple evaluators are created when the passed in equation contains an equals sign.
A clue's list of evaluators is available as `clue.evaluators`.

An evaluator's list of free variables is available as `evaluator.vars`. 
You can get the value an evaluator for a given set of values by calling
`evaluator(dictionary)`, where the `dictionary` argument is a mapping from variables
to the integer value of those variable.
If the result is a positive integer, it is returned as a string. 
Otherwise, `None` is returned. 

NOTE: We do not yet handle the expression throwing an error.
Should this be fixed?


#### The Generator
The generator is a function that takes a `Clue` argument (mainly for its length) and returns possible clue values.
The returned clue values can either be an integers or a string.
The generator returns either an iterator, a list, or a generator of such values.

In very rare cases, the generator can be `None`.
This is described later.

The file `Generators.py` contains several generators of the sort that frequently appear in Magpie puzzles.
It also contains generators that return a pre-calculated list and generators that just return every possible value.
The latter probably shouldn't be used for clues longer than length 6.


#### Non-standard clues and subclassing
If your grid is not actually a rectangle or your clues go into the grid in an unusual way, you can subclass `Clue`.

The code assumes that across clues start at the indicated location and move right
(increasing the second index of the location),  
and that down clues start at the indicated location and move down (increasing the first index). 
If your puzzle has different rules, you should subclass `Clue` and override the method `generate_location_list`
to generate the list of locations.

TODO: Verify length?  Verify first element is base_location? 


### The clue list

A `ClueList` gathers together a set of clues and creates information about them as a set.

For the `EquationSolver`, there is a convenience function that lets you copy and paste the equations 
from the puzzle and directly generate a clue list.

In general, you create a `ClueList` by passing the initializer a list of the puzzle's clues.

    clue_list = ClueList(sequence_of_clues)
 
#### Subclassing ClueList
    
There are a few reasons to subclass `ClueList`:

* In most puzzles, the first digit of an answer cannot be zero.
In some puzzles, there may be further constraints.
    * The user can override `is_zero_allowed(location)` if there are alternative constraints.
The default implementation returns `True` when the location is not the starting location of any clue.

    * Some puzzles may have other constraints on digits.
The user can override `get_allowed_regexp(location)` to indicate the allowable values. 
The default implementation calls `is_zero_allowed(location)` above and returns
either `"."` or `"[^0]"`, respectively, on a `true` or `false` result, respectively.
Any appropriate regexp that matches at most a single character is allowed.

* `ClueList` is responsible for printing the grid once a solution has been found.
The default implementation of `draw_grid` just calls the `DrawGrid` utility with the arguments it has been passed.
By overriding this method, the user can intervene and modify the arguments before calling `super().draw_grid(...)`.

Among some examples for overriding `draw_grid` are:

* Replacing the digits in the result with the letters of a key word
* Adding shading to the grid
* Changing the location of thick bars.

#### Verification of the grid.

`ClueList` contains three very important verification functions:

* `clue_list.verify_is_180_symmetric`: 
The grid should look the same when it is rotated 180°.
The method throws an assertion error if that is not the case.

* `clue_list.verify_is_four_fold_symmetric`: 
The grid should look the same if it is rotated either 90° or 180°.
The method throws an assertion error if that is not the case.

* `clue_list.verify_is_vertically_symmetric`: 
The grid should look the same in a mirror as it does normally.

When first creating a grid, it is highly recommended that you write:

    clue_list = ....
    clue_list.plot_board({})
    # replace the next line with whatever symmetry is appropriate
    clue_list.verify_is_180_symmetric() 
    
It is extremely easy to make a mistake when describing the grid.
Asking Python to show you a picture of the empty 
board and to verify that it has the symmetry you expect is sure to save you a lot of grief.


## Solving crossword puzzles

### The equation solver

The `EquationSolver` is by far the simpler of the two.
A typical call to create an equation solver looks like the following:

    EquationSolver(clue_list, items=list(range(1, 27)))

The arguments indicate:

* The clue list for the puzzle, 

* The allowable values for the variables are 1..26 inclusive, and (by default) each value can be used at most once.
\[Note, the values in the list must be distinct.
See below if variable values can be repeated.]

* Each equation must (by default) yield a distinct value.
If duplicate values are allowed, then add the keyword argument `allow_duplicates=True` to the argument list.

There are three methods you may want to override:

* `check_solution()` is called when the solver has found a tentative solution.
The default implementation simply returns `True`, but additional puzzle-specific verification that is not easy
to otherwise specify can be performed here.

* `show_solution()` is called when `check_solution()` returns `True`.
It prints out the values of the variables and draws the filled-in grid.
Users can augment or replace this behaviour.

* `get_letter_values()` is called to find all possible values to assign to letters, 
given previously existing  assignments.
You must override this method if the puzzle uses something more complicated than 
"each variable must get a distinct value from the list passed as the `item=` argument". 
See Magpie195 for an example.

The solver is run by calling `solver.run()`.
Information about the steps the solver is performing can
be seen by adding the arguemnt `debug=True`.

    
#### How it works.

This solver first performs a one-time determination of the order in which to solve the clues' evaluators.
Most clues will have a single evaluator, but some clues may have multiple.

It repeatedly ranks the evaluators (and their corresponding clues) based on the following criteria:

1. Which clue has the fewest number of letters not yet assigned a value?
1. If there is a tie, which of those evaluators belongs to a clue that has the largest percentage of squares 
that intersect with already selected evaluators and their clues?
1. If there is a tie, which belongs to the longest clue?
1. If there is still a tie, a random one is chosen

After each "best remaining" evaluator is chosen, each of the not-yet-selected
evaluators needs to be re-evaluated for the next round; 
some of its letters may have been assigned by the just selected clue, 
and some of its clue's squares may intersect the just chosen evaluator's clue.

The solver performs a search through the evaluators in this pre-calculated order.
As a result, when the solver looks a evaluator and its clue, it has already determined 
which letters in the clue have already been assigned, 
which letters still need to have a value assigned to them, and 
which digits of its answer have been filled by previous answers.

Given this order for solving the evaluators, the solver calls the following recursive algorithm, starting with n = 0

1. If n is the the number of evaluators, we have a tentative solution.
Call `check_solution()`, and if it returns `True`, call `show_solution()` and return.

1. Find the n-th evaluator in the order we are solving them, as determined above.

1. Calculate a regular expression that matches legal values for this evaluator's clue, taking into account 
   - squares filled by previously solved clues that intersect this one,
   - squares that can't contain 0 because they are the first digit of this or another clue, and 
   - other interesting facts determined by `get_allowed_regexp()`.

1. Call `get_letter_values()` to determine all possible values that this evaluator's still unknown variables can take. 
For each set of possible values for the variables:
    1. Evaluate the expression using the variables and their values.
    1. If the value of the expression is an illegal result, or if the value
       doesn't match the regular expression, skip these values and try again.
    1. If the value of the expression is a value we're already using for a previous evaluator and `not use_duplicates`
       then continue
    1. Add the current variables and values to the set of known value
    1. Recursively run this algorithm with n + 1
    1. Remove the current variables and values from the set of known values


### The Contraint Solver

A typical call to create a constraint solver looks like the following:

    EquationSolver(clue_list)

The arguments indicate:

* The clue list for the puzzle, 

* Each clue must have a distinct value.
If duplicate values are allowed, then add the keyword argument `allow_duplicates=True` to the argument list.

There are two primary ways of specifying constraints:

* When you create a `Clue` you specify a generator which shows the possible values that the clue can have 
with no other considerations.
For example "This clue is a square", "This clue is prime", 
"This clue is a multiple of 17" are all constraints that are specified in the generator.

* Certain constraints indicate a relationship between two clues.
These are added to the `ConstraintSolver`. 
For example the following two lines force d3 to be a multiple of a1, and force d3 to be the product of d1 and d2.


    solver.add_constraint(('a1', 'd3'), lambda x, y: int(y) % int(x) == 0)
    solver.add_constraint(('d1', 'd2', 'd3'),  
        lambda x, y, z: int(x) * int(y) == int(z))
        
Note that the arguments passed to the predicate are strings, and 
the predicate is responsible for converting them to integers, if necessary.
The items in the initial tuple can either be a `Clue` or the name of a clue.
The predicate must take as many arguments a there are items in the tuple; 
the arguments are bound, in order, to the values of the corresponding clue.

                
There are three methods you may want to override:

* You can override `check_solution()`, which is called then the solver has found a tentative solution.
The default implementation just returns `True`, but you can perform additional puzzle-specific tests.
This is a good place to test conditions like: "This clue must be the some of all digits in the puzzle" that can't
easily be tested otherwise.

You may also want to override `show_solution()`, which is called when `check_solution()` returns true.
The default implementation draws a grid, but you can replace or augment this functionality.

The solver is then run by calling `solver.run()`.
More information about the steps the solver is performing can be seen by adding the argument `debug=True`.


#### Advanced techniques 

##### Clues with a generator of `None`

It is rare, but legal to give a clue a generator of `None`.
This clue is completely ignored by the solver.
TODO:  Can we set it up to be handled by a constraint?

In some rarer cases, it is necessary to delay the value of a clue until `check_solution()`.
For example, if a clue's value is listed as "the sum of all the digits in the puzzle" or "a seven-digit non-prime",  
it's probably best to wait until `check_solution()` to see if a reasonable value has already been put into the grid
by crossing clues.

##### Subclassing `string`

Sometimes, a clue value contains information beyond just its value.
For example, value must keep track of some particular fact about how it was generated, 
and other seemingly identical strings might have different information associated with them.
Python allows the user to subclass string.
See XXX for an example of how this is done.

Your generators should produce instances of your string subclass rather than integers or normal strings.
`ConstraintSolver` will never produce new clue values on its own.
When `check_solution()` and constraints are called you can be assured that all
clue values, will be your subclass of string, and you can freely treat them as objects of that type.

#### How it works

For each clue, the generator is called to calculate the set of all possible answers for that clue.
 This list of clues is filtered by taking into account `is_zero_allowed()` and `get_allowed_regexp()` for each location, thereby ensuring that there are no zeros where they aren't allowed.

The following recursive algorithm is then followed.
We have as input a dictionary of clues, and for each clue a set of possible values that the clue can take.

1. If the dictionary is empty, we are done. 
Call `check_solution()`, and if that returns `true`, call `show_solution()`. 
Return.

1. Find the clue that has the smallest number of possible values.
If there is a tie, use the clue that has the longest length.
If there is still a tie, pick one at random.

1. If the number of possible values for this clue is zero, then return.

1. For each possible value that this clue can take (the "current value"), do the following:
   1. If this current value is a duplicate, continue.
   
   1. Look at all constraints associated with this clue.
   For any constraint that has all but one clue assigned a value, restrict that clue
   to only have values that satisfy the constraint.
   Continue to the next "current value"
   if some constraint yields the empty set.
   
   1. Create a dictionary that is a copy of the current dictionary except:
      * The current clue is removed as a key
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

The grid is a cube, and there are "through" clues as well as clues that go across or down a single layer.
In addition, there are rules about a clue going off the edge of its own layer.

To solve this, we model the 4x4x4 cube as a 16x4 rectangle, and subclass `Clue` in order to implement the clue rules.
The solution is straightforward

`ClueList` is overridden so that the generated grid appears more pleasing.
We don't want the normal thick bars printed out.
Instead, we just want thick bars as a break between each of the 4x4 layers.
In addition, once we read the hidden message and know the secret ten-letter word, 
we print the grid a second time with letters replacing the digits in the grid.

### Magpie 195
A straightforward set of equations that we could solve by copy and paste.

### Magpie 197
A straightforward `EquationSolver` that we could solve by copy and paste.

### Magpie 201
A straightforward `EquationSolver` that we could solve by copy and paste.
However we override `draw_grid` once we learn that all 3s, 7s, and 8s need to be shaded.


## ConstraintSolver

### Listener 4542

Each clue is labelled by a letter.
Each clue has a number and an equation associated with it.
The number gives the number of letters in the English spelling of the clue, and the equation indicates the sum of the distinct letters (A=1, B=2, etc) of the English spelling.

The solver is set up as a `ConstraintSolver`, where the generator lists all numbers that match the length of the clue
and the specified length of the English spelling of the clue.

Each clue also includes an equation, which gets turned into one or more evaluators.
Each evaluator is turned into a constraint by recognizing that each evaluator's unbound variables are also the names
of the clues that this constraint applies to.
A python wrapper function converts the argument list expected by a constraint into the argument list expected by an evaluator.

### Listener 4555

A `ConstraintSolver` with extraordinarily complicated interplay between the clues.

This is one of the few uses of `generator=None`.
Since the only thing we know about D7 is that it is a 7-digit non-prime, it was easier to just test it after all the other clues were assigned, rather than to enumerate all several million non-primes.

### MagPie 145

Interesting rules for setting up the generators, but a straightforward solve.

### Magpie 146

Actually two puzzles.
The first involves finding out the values of the entries, and the second involves fitting the entries into the grid.
The second puzzle is a straightforward `ConstraintSolver`

More about the first puzzle. . .

### Magpie 153
A complicated ConstraintSolver, with lots of work in the post fixup because lots of clues must be multiples of lots of other clues

### Magpie 196
A straightfoward `ConstraintSolver`, except the generators had to be adjusted for non-base-10

### Magpie 198
A straighforward `ConstraintSolver`, except that every across clue has a constraint with every other across clue, and every down clue has a constraint with every other down clue.
This lets the puzzle be solved quickly!

### Magpie 199
A `ConstraintSolver` in which the hard part was determining the initial possible values for each clue.
Much math was involved, but once we figured out the initial values, the solution was straightforward.

### Magpie 200
A `ConstraintSolver` in which we had to subtype `string`.
Each answer must be unique in the way it was produced.
Hence each clue has a constraint against every other clue.

## Other puzzles.

### Magpie 149
One of a kind. Worth describing?

### Magpie 194
An amazing extremely hard puzzle that didn't fit in with us. 
Lots of logic.






`







