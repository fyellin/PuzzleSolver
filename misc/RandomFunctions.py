import heapq
import itertools
import math
import operator
from collections import deque
from collections.abc import Iterable, Mapping, Sequence, Callable

class FakeArray[S](Sequence):
    def __init__(self, length: int, getter: Callable[[int], S]):
        self.length = length
        self.getter = getter

    def __getitem__(self, i: int) -> S:
        return self.getter(i)

    def __len__(self):
        return self.length

class MaxHeapObj:
    def __init__(self, val): self.val = val
    def __lt__(self, other): return self.val > other.val
    def __eq__(self, other): return self.val == other.val
    def __str__(self): return str(self.val)


class MinHeap:
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
    """Manacher's algorithm for finding odd-length palindromes"""
    d1 = {}
    l = 0
    r = -1
    for i in range(length):
        ## AI says that r - i + 1 should be r - 1.  Check later
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
    """Manacher's algorithm for finding even-length palindromes"""
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
    """Find rightmost value less than x"""
    i = bisect_left(a, x)
    if i:
        return a[i-1]
    raise ValueError


def find_le(a, x):
    """Find the rightmost value less than or equal to x"""
    i = bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError

def find_gt(a, x):
    """Find the leftmost value greater than x"""
    i = bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def find_ge(a, x):
    """Find the leftmost item greater than or equal to x"""
    i = bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


class Dijkstra[State]:
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[tuple[State, int]]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> tuple[int, State | None]:
        minimum_map = {self.start: 0}
        queue: list[tuple[int, int, State]] = [(0, 0, self.start)]
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


class FastDijkstra[State]:
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[State]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> tuple[int, State | None]:
        minimum_map = {self.start: 0}
        queue: deque[tuple[int, int, State]] = deque([(0, 0, self.start)])
        seen = added = ignored = 0
        previous_distance = -1

        while queue:
            this_distance, _, this_state = queue.popleft()
            seen += 1
            if verbose >= 1 and previous_distance < this_distance:
                print(f"# Distance is now {this_distance} (queue={len(queue)})")
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
                              f"{this_distance} + 1 ≥ {minimum_map[new_state]}")
        print("# ❌ FAILURE")
        return this_distance - 1, None


class DijkstraExtended[State]:
    start: State

    def __init__(self, start: State):
        self.start = start

    def neighbor(self, state: State) -> Iterable[tuple[State, int]]:
        ...

    def is_done(self, state: State) -> bool:
        ...

    def run(self, verbose: int = 0) -> tuple[State | None, Sequence[Sequence[State]]]:
        minimum_map = {self.start: 0}
        queue: list[tuple[int, int, State]] = [(0, 0, self.start)]
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

    def get_chains(self, state: State, whence_map: Mapping[State, Sequence[State]]) -> list[list[State]]:
        next_states = whence_map.get(state, None)
        if next_states is None:
            return [[state]]
        else:
            return [[*chain, state] for next_state in next_states for chain in self.get_chains(next_state, whence_map)]


class Fenwick:
    #  LSB(X)  is X & -X
    #  X - LSB(X)  is  X & (X - 1)
    #  X + LXB(X + 1) is X | (X + 1)
    A: list[int]
    length: int
    power_of_two: int

    def __init__(self, A: list[int]) -> None:
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


def apd(A, n: int):
    """
    Compute the shortest-paths lengths.

    This function computes the shortest-path lengths of a given adjacency matrix
    using a recursive algorithm. It iteratively evaluates direct and indirect
    connections between nodes within the adjacency matrix and calculates the
    desired result following specific conditions based on degree and path sums.

    :param A: The adjacency matrix represented as a 2D array or list of lists,
        where A[i][j] indicates the presence or absence of a direct connection
        between nodes i and j.
    :type A: list or numpy.ndarray
    :param n: The number of nodes in the adjacency matrix.
    :return: A 2D array containing the shortest-paths lengths. Each entry D[i][j]
        represents the computed shortest-path distance between node i and node j.
    :rtype: numpy.ndarray
    """
    from numpy import array
    """Compute the shortest-paths lengths."""
    if all(A[i][j] for i in range(n) for j in range(n) if i != j):
        return A
    Z = A ** 2
    B = array([
        [1 if i != j and (A[i][j] == 1 or Z[i][j] > 0) else 0 for j in range(n)]
    for i in range(n)])
    T = apd(B, n)
    X = T@A
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


def number_to_words(n: int) -> str:
    """Convert a number (0 to 999,999) to words."""
    if not 0 <= n < 1_000_000:
        raise ValueError("Number must be between 0 and 999,999")

    if n == 0:
        return "zero"

    # Basic number words
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
    teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
             "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty",
            "ninety"]

    def convert_below_thousand(num):
        """Convert a number less than 1000 to words."""
        if num == 0:
            return ""
        elif num < 10:
            return ones[num]
        elif num < 20:
            return teens[num - 10]
        elif num < 100:
            return tens[num // 10] + ("-" + ones[num % 10] if num % 10 != 0 else "")
        else:  # num < 1000
            hundred_part = ones[num // 100] + " hundred"
            remainder = num % 100
            if remainder == 0:
                return hundred_part
            return hundred_part + " " + convert_below_thousand(remainder)

    # Handle thousands
    thousands = n // 1000
    remainder = n % 1000

    result = []
    if thousands > 0:
        result.append(convert_below_thousand(thousands) + " thousand")
    if remainder > 0:
        result.append(convert_below_thousand(remainder))

    return " ".join(result)
