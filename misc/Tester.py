import functools
import collections
import copy
import functools
import heapq
import itertools
import math
import operator
import random
from collections import deque, defaultdict
from typing import List, Tuple, Set, Optional, Dict, Iterable, Callable, Sequence, TypeVar, Hashable, Generic, Any, \
    Mapping, Iterator

ArrayType = TypeVar("ArrayType")
class FakeArray(collections.abc.Sequence, Generic[ArrayType]):
    def __init__(self, length: int, getter: Callable[[int], ArrayType]):
        self.length = length
        self.getter = getter

    def __getitem__(self, i: int) -> ArrayType:
        return self.getter(i)

    def __len__(self):
        return self.length

class MaxHeapObj(object):
  def __init__(self, val): self.val = val
  def __lt__(self, other): return self.val > other.val
  def __eq__(self, other): return self.val == other.val
  def __str__(self): return str(self.val)

class MinHeap(object):
  def __init__(self): self.h = []
  def heappush(self, x): heapq.heappush(self.h, x)
  def heappop(self): return heapq.heappop(self.h)
  def __getitem__(self, i): return self.h[i]
  def __len__(self): return len(self.h)

class MaxHeap(MinHeap):
  def heappush(self, x): heapq.heappush(self.h, MaxHeapObj(x))
  def heappop(self): return heapq.heappop(self.h).val
  def __getitem__(self, i): return self.h[i].val


def get_d1(s, length):
    d1 = {}
    l = 0;
    r = -1
    for i in range(length):
        k = 1 if i > r else min(d1[l + r - i], r - i + 1)
        while (0 <= i - k and i + k < length and s[i - k] == s[i + k]):
            k += 1
        d1[i] = k
        k -= 1
        if i + k > r:
            l = i - k
            r = i + k
    return d1


def get_d2(s, length):
    d2 = {}
    l = 0
    r = -1
    for i in range(length):
        k = 0 if i > r else min(d2[l + r - i + 1], r - i + 1)
        while (0 <= i - k - 1 and i + k < length and s[i - k - 1] == s[i + k]):
            k += 1
        d2[i] = k
        k -= 1
        if (i + k > r):
            l = i - k - 1
            r = i + k
    return d2


Row = TypeVar('Row', bound=Hashable)
Constraint = TypeVar('Constraint', bound=Hashable)
class DancingLinks(Generic[Row, Constraint]):
    row_to_constraints: Dict[Row, List[Constraint]]
    optional_constraints: Set[Constraint]
    inclusive_contraints: Set[Constraint]
    constraint_to_rows: Dict[Constraint, Set[Row]]
    solutions: List[List[Row]]

    def __init__(self, constraints: Dict[Row, List[Constraint]], *,
                 optional_constraints: Optional[Set[Constraint]] = None,
                 inclusive_constraints: Optional[Set[Constraint]] = None):
        """The entry to the Dancing Links code.  constraints should be a dictionary.  Each key
        is the name of the row (something meaningful to the user).  The value should
        be a list/tuple of the row_to_constraints satisfied by this row.

        The row names and constraint names can be anything immutable and hashable.
        Typically they are strings, but feel free to use whatever works best.
        """
        self.row_to_constraints = constraints
        self.optional_constraints = optional_constraints or set()
        self.inclusive_constraints = inclusive_constraints or set()

    def solve(self) -> List[List[Row]]:
        # Create the cross reference giving the rows in which each constraint appears
        constraint_to_rows: Dict[Constraint, Set[Row]] = collections.defaultdict(set)
        for row, constraints in self.row_to_constraints.items():
            for constraint in constraints:
                constraint_to_rows[constraint].add(row)

        self.optional_constraints = {x for x in self.optional_constraints if x in constraint_to_rows}
        unused_constraints = {x for x in self.optional_constraints if len(constraint_to_rows[x]) == 1}
        for constraint in unused_constraints:
            row = constraint_to_rows.pop(constraint).pop()
            self.row_to_constraints[row].remove(constraint)
            self.optional_constraints.remove(constraint)

        runner = copy.copy(self)

        runner.constraint_to_rows = constraint_to_rows
        runner.solutions = []
        runner.__solve_constraints_iterative()
        return runner.solutions

    def __solve_constraints_iterative(self) -> int:
        # Note that "depth" is meaningful only when debugging.
        stack: List[Tuple[Callable[..., None], Sequence[Any]]] = []

        def run():
            stack.append((find_minimum_constraint, (0,)))
            while stack:
                function, args = stack.pop()
                function(*args)

        def find_minimum_constraint(depth: int) -> None:
            try:
                count, _, constraint = min((len(rows), 0.0 * random.random(), constraint)
                                           for constraint, rows in self.constraint_to_rows.items()
                                           if constraint not in self.optional_constraints)
            except ValueError:
                # There is nothing left but optional constraints.  We have a solution!
                # row_cleanup on the stack indicates that we are currently working on that item
                solution = [args[1] for (func, args) in stack if func == row_cleanup]
                self.solutions.append(solution)
                return

            if count > 0:
                stack.append((look_at_constraint, (constraint, depth)))
            else:
                pass

        def look_at_constraint(constraint: Constraint, depth: int) -> None:
            # Look at each possible row that can resolve the constraint.
            rows = self.__cover_constraint(constraint)
            count = len(rows)

            stack.append((constraint_cleanup, (constraint, rows)))
            entries = [(look_at_row, (constraint, row, index, count, depth)) for index, row in enumerate(rows, start=1)]
            stack.extend(reversed(entries))

        def look_at_row(constraint: Constraint, row: Row, index: int, count: int, depth: int) -> None:
            cleanups = [(row_constraint, self.__cover_constraint(row_constraint))
                        for row_constraint in self.row_to_constraints[row]
                        if row_constraint != constraint]

            # Remember we are adding things in reverse order.  Recurse on the smaller subproblem, and then cleanup
            # what we just did above.
            stack.append((row_cleanup, (cleanups, row)))
            stack.append((find_minimum_constraint, (depth + (count > 1),)))

        def row_cleanup(cleanups: List[Tuple[Constraint, Set[Row]]], _row: Row, ) -> None:
            for constraint, rows in reversed(cleanups):
                self.__uncover_constraint(constraint, rows)

        def constraint_cleanup(constraint: Constraint, rows: Set[Row]) -> None:
            self.__uncover_constraint(constraint, rows)

        return run()

    def __cover_constraint(self, constraint: Constraint) -> Set[Row]:
        rows = self.constraint_to_rows.pop(constraint)
        for row in rows:
            # For each constraint in this row about to be deleted
            for row_constraint in self.row_to_constraints[row]:
                # Mark this feature as now longer available in the row,
                # unless we're looking at the feature we just chose!
                if row_constraint != constraint:
                    self.constraint_to_rows[row_constraint].remove(row)
        return rows

    def __uncover_constraint(self, constraint: Constraint, rows: Set[Row]) -> None:
        for row in rows:
            for row_constraint in self.row_to_constraints[row]:
                if row_constraint != constraint:
                    self.constraint_to_rows[row_constraint].add(row)
        self.constraint_to_rows[constraint] = rows


def bisect_left(getter: Callable[[int], int], x: int, lo: int, hi: int) -> int:
    while lo < hi:
        mid = (lo+hi)//2
        if getter(mid) < x: lo = mid+1
        else: hi = mid
    return lo

def bisect_right(getter: Callable[[int], int], x: int, lo: int, hi: int) -> int:
    while lo < hi:
        mid = (lo+hi)//2
        if x < getter(mid): hi = mid
        else: lo = mid+1
    return lo

def find_lt(a, x):
    'Find rightmost value less than x'
    i = bisect_left(a, x)
    if i:
        return a[i-1]
    raise ValueError

def find_le(a, x):
    'Find rightmost value less than or equal to x'
    i = bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError

def find_gt(a, x):
    'Find leftmost value greater than x'
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def reverse_in_place(node: 'ListNode') -> Tuple['ListNode', 'ListNode']:
    previous = None
    last = current = node
    following = current.next

    while current:
        current.next = previous
        previous = current
        current = following
        if current:
            following = following.next

    return previous, last


State = TypeVar('State')
class Dijkstra(Generic[State]):
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[Tuple[State, int]]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> Tuple[int, Optional[State]]:
        minimum_map = dict([(self.start, 0)])
        queue: List[Tuple[int, int, State]] = [(0, 0, self.start)]
        seen = added = ignored = 0
        previous_distance = -1

        while queue:
            this_distance, _, this_state = heapq.heappop(queue)
            seen += 1
            if verbose >= 1 and previous_distance < this_distance:
                print(f"# Distance is now {this_distance}")
                previous_distance = this_distance
            if minimum_map[this_state] < this_distance:
                # We've already seen this state with a smaller distance.  No use reprocessing
                ignored += 1
                if verbose >= 2:
                    print(f"#    ❌ Already saw {this_state} (distance={minimum_map[this_state]})")
                continue
            if verbose >= 2:
                print(f"#     ✔ Looking at {this_state}")
            if self.is_done(this_state):
                print(f"# ✔ {this_state} distance={this_distance} "
                      f"seen={seen} added={added}, ignored={ignored}")
                return this_distance, this_state

            for new_state, distance in self.neighbor(this_state):
                new_distance = this_distance + distance
                # new_distance = max(this_distance, distance)
                if new_distance < minimum_map.get(new_state, math.inf):
                    minimum_map[new_state] = new_distance
                    added += 1
                    heapq.heappush(queue, (new_distance, added, new_state))
                    if verbose >= 3:
                        print(f"#       + {new_state} at {new_distance} = {this_distance} + {distance}")
                else:
                    if verbose >= 3:
                        print(f"#       - {new_state} at {new_distance} = "
                              f"{this_distance} + {distance} > {minimum_map[new_state]}")
        print("# ❌ FAILURE")
        return this_distance - 1, None

State = TypeVar('State')
class FastDijkstra(Generic[State]):
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[State]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> Tuple[int, Optional[State]]:
        minimum_map = dict([(self.start, 0)])
        queue: deque[tuple[int, int, State]] = deque([(0, 0, self.start)])
        seen = added = ignored = 0
        previous_distance = -1

        while queue:
            this_distance, _, this_state = queue.popleft()
            seen += 1
            if verbose >= 1 and previous_distance < this_distance:
                print(f"# Distance is now {this_distance}")
                previous_distance = this_distance
            if minimum_map[this_state] < this_distance:
                # We've already seen this state with a smaller distance.  No use reprocessing
                ignored += 1
                if verbose >= 2:
                    print(f"#    ❌ Already saw {this_state} (distance={minimum_map[this_state]})")
                continue
            if verbose >= 2:
                print(f"#     ✔ Looking at {this_state}")
            if self.is_done(this_state):
                print(f"# ✔ {this_state} distance={this_distance} "
                      f"seen={seen} added={added}, ignored={ignored}")
                return this_distance, this_state

            for new_state in self.neighbor(this_state):
                new_distance = this_distance + 1
                # new_distance = max(this_distance, distance)
                if new_distance < minimum_map.get(new_state, math.inf):
                    minimum_map[new_state] = new_distance
                    added += 1
                    queue.append((new_distance, added, new_state))
                    if verbose >= 3:
                        print(f"#       + {new_state} at {new_distance} = {this_distance} + 1")
                else:
                    if verbose >= 3:
                        print(f"#       - {new_state} at {new_distance} = "
                              f"{this_distance} + 1 > {minimum_map[new_state]}")
        print("# ❌ FAILURE")
        return this_distance - 1, None


State = TypeVar('State')
class DijkstraExtended(Generic[State]):
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[Tuple[State, int]]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> Tuple[Optional[State], Sequence[Sequence[State]]]:
        minimum_map = dict([(self.start, 0)])
        queue: List[Tuple[int, int, State]] = [(0, 0, self.start)]
        seen = added = ignored = 0
        previous_distance = -1
        whence_map = {}

        while queue:
            this_distance, _, this_state = heapq.heappop(queue)
            seen += 1
            if verbose >= 1 and previous_distance < this_distance:
                print(f"# Distance is now {this_distance}")
                previous_distance = this_distance
            if minimum_map[this_state] < this_distance:
                # We've already seen this state with a smaller distance.  No use reprocessing
                ignored += 1
                if verbose >= 2:
                    print(f"#    ❌ Already saw {this_state} (distance={minimum_map[this_state]})")
                continue
            if verbose >= 2:
                print(f"#     ✔ Looking at {this_state}")
            if self.is_done(this_state):
                print(f"# ✔ {this_state} distance={this_distance} "
                      f"seen={seen} added={added}, ignored={ignored}")
                return this_state, self.get_chains(this_state, whence_map)

            for new_state, distance in self.neighbor(this_state):
                new_distance = this_distance + distance
                # new_distance = max(this_distance, distance)
                if new_distance < minimum_map.get(new_state, math.inf):
                    minimum_map[new_state] = new_distance
                    whence_map[new_state] = [this_state]
                    added += 1
                    heapq.heappush(queue, (new_distance, added, new_state))
                    if verbose >= 3:
                        print(f"#       + {new_state} at {new_distance} = {this_distance} + {distance}")
                elif new_distance == minimum_map.get(new_state, math.inf):
                    whence_map[new_state].append(this_state)
                else:
                    if verbose >= 3:
                        print(f"#       - {new_state} at {new_distance} = "
                              f"{this_distance} + {distance} > {minimum_map[new_state]}")
        print("# ❌ FAILURE")
        return None, []

    def get_chains(self, state: State, whence_map: Mapping[State, Sequence[State]]) -> List[List[State]]:
        next_states = whence_map.get(state, None)
        if next_states is None:
            return [[state]]
        else:
            return [[*chain, state] for next_state in next_states for chain in self.get_chains(next_state, whence_map)]


class Fenwick:
    #  LSB(X)  is X & -X
    #  X - LSB(X)  is  X & (X - 1)
    #  X + LXB(X + 1) is X | (X + 1)
    A: List[int]
    length: int
    power_of_two: int

    def __init__(self, A: List[int]) -> None:
        self.A = A
        self.length = length = len(A)
        for i in range(length):
            j = i | (i + 1)
            if j < length:
                A[j] += A[i]
        temp = length
        while temp != (temp & -temp):
            temp = temp & (temp - 1)
        self.power_of_two = temp


    def prefix_sum(self, i):
        """Returns elements from 0 to i - 1"""
        total = 0
        while i > 0:
            total += self.A[i - 1]
            i = i & (i - 1)
        return total

    def add(self, i, delta) -> None:
        while i < len(self.A):
            self.A[i] += delta
            i = i | (i + 1)

    def range_sum(self, i, j):
        total = 0
        while (j > i):
            total += self.A[j - 1]
            j = j & (j - 1)
        while (i > j):
            total -= self.A[i - 1]
            i = i & (i - 1)
        return total

    def __getitem__(self, i: int) -> int:
        return self.range_sum(i, i + 1)

    def __setitem__(self, i: int, val: int) -> None:
        self.add(i, val - self[i])

    def rank_query(self, value):
        """Find the largest i with prefix_sum(i) <= value"""
        j = self.power_of_two
        i = 0
        while j > 0:
            if i + j <= self.length and self.A[i + j - 1] <= value:
                value -= self.A[i + j - 1]
                i += j
            j >>= 1
        return i


Node = TypeVar('Node', bound=Hashable)
class UnionFind(Generic[Node]):
    parent: Dict[Node, Node]
    rank: Dict[Node, int]

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x: Node):
        parent = self.parent
        parent.setdefault(x, x)
        root = x
        while (next := parent[root]) != root:
            root = next
        while (next := parent[x]) != root:
            x, parent[x] = next, root
        return root

    def union(self, x: Node, y: Node):
        x = self.find(x)
        y = self.find(y)
        if x != y:
            rankx = self.rank.setdefault(x, 1)
            ranky = self.rank.setdefault(y, 1)
            if rankx > ranky:
                # We dont' swap rankx and ranky because after this, we only care if they're equal
                x, y = y, x
            self.parent[x] = y
            if rankx == ranky:
                self.ranky = ranky + 1



class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    @staticmethod
    def fromArray(values: Sequence[Any]) -> 'TreeNode':
        if not values:
            return None
        iterator = iter(values)
        result = TreeNode(next(iterator))
        queue = collections.deque([result])

        while queue:
            this, left, right = queue.popleft(), next(iterator,  None), next(iterator, None)
            if left is not None:
                this.left = TreeNode(left)
                queue.append(this.left)
            if right is not None:
                this.right = TreeNode(right)
                queue.append(this.right)

        return result

    def toArray(self):
        result = []
        queue = collections.deque([result])
        while queue:
            this = queue.popleft()
            if this is None:
                result.append(None)
            else:
                result.append(this.val)
                queue.extend((this.left, this.right))
        while len(result) >= 3 and result[-2] is None and result[-1] is None:
            result.pop(); result.pop()

    def __str__(self):
        if self.left is None and self.right is None:
            return f'<{self.val}>'
        left = str(self.left) if self.left is not None else 'X'
        right = str(self.right) if self.right is not None else 'X'
        return f'<{self.val} {left} {right}>'

    def __repr__(self):
        return str(self)

class Link:
    prev: 'Link'
    next: 'Link'
    key: int
    value: int

    def __init__(self, prev, next, key, value):
        self.prev = prev
        self.next = next
        self.key = key
        self.value = value

class Link:
    prev: 'Link'
    next: 'Link'
    key: int
    value: int

    def __init__(self, prev, next, key, value):
        self.prev = prev
        self.next = next
        self.key = key
        self.value = value

    def __str__(self):
        return f"<{self.key}={self.value}>"

    def __repr__(self):
        return str(self)




def apd(A, n: int):
    from numpy import array
    """Compute the shortest-paths lengths."""
    if all(A[i][j] for i in range(n) for j in range(n) if i != j):
        return A
    Z = A ** 2
    B = array([
        [1 if i != j and (A[i][j] == 1 or Z[i][j] > 0) else 0 for j in range(n)]
    for i in range(n)])
    T = apd(B, n)
    X = T*A
    degree = [sum(A[i][j] for j in range(n)) for i in range(n)]
    D = array([
        [2 * T[i][j] if X[i][j] >= T[i][j] * degree[j] else 2 * T[i][j] - 1 for j in range(n)]
    for i in range(n)])
    return D


class Trie:
    def __init__(self, words, index):
        self.index = index
        self.words = words
        self.is_prefix_leaf = len(words[0]) == index
        self.is_normal_leaf = len(words) == 1
        self.dictionary = None

    def build_dictionary(self):
        dictionary = {}
        for key, values in itertools.groupby(self.words, operator.itemgetter(self.index)):
            dictionary[key] = Trie(list(values), self.index + 1)
        self.dictionary = dictionary

    @staticmethod
    def lookup(word, trie):
        for index, char in enumerate(word):
            if trie.is_prefix_leaf:
                return trie.words[0]
            elif trie.is_normal_leaf:
                trie_word = trie.words[0]
                return trie_word if word.startswith(trie_word) else word
            if trie.dictionary is None:
                trie.build_dictionary()
            trie = trie.dictionary.get(word[index])
            if trie is None:
                return word
        return word


def palindrome(length) -> Iterator[str]:
    """Returns palindromes"""

    half_length = (length + 1) // 2
    is_even = (length & 1) == 0
    multiplier = 10 ** (length // 2)
    for i in range(10 ** (half_length - 1), 10 ** half_length):
        left = str(i)
        right = left[::-1]
        j = int(right if is_even else right[1:] if length > 1 else '0')
        value = i * multiplier + j
        value2 = value * value
        temp = str(value2)
        if temp == temp[::-1]:
            yield value2


class Solution:
    def shoppingOffers(self, price: List[int], special: List[List[int]], needs: List[int]) -> int:

        def is_good_offer(offer):
            separate_price = sum(p * off for p, off in zip(price, offer))
            discount_price = offer[-1]
            return discount_price < separate_price

        special = list(filter(is_good_offer, special))

        class MyDijkstra(Dijkstra):
            def is_done(self, state):
                return all(x == 0 for x in state)

            def neighbor(self, state: State) -> Iterable[Tuple[State, int]]:
                for index, value in enumerate(state):
                    if value > 0:
                        yield (*state[:index], value - 1, *state[index + 1:]), price[index]
                    for offer in special:
                        if all(off <= val for off, val in zip(offer, state)):
                            new_state = tuple(val - off for off, val in zip(offer, state))
                            yield new_state, offer[-1]

        solver = MyDijkstra(tuple(needs))
        result, state = solver.run()
        return result


if __name__ == '__main__':
    temp = set()

    heapq.merge
