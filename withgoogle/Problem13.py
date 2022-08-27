from __future__ import division

import collections
import itertools
import math
from collections import deque

DELTA = [(1, 2)]
DELTA += [(x, -y) for x, y in DELTA]
DELTA += [(-x, y) for x, y in DELTA]
DELTA += [(y, x) for x, y in DELTA]
def solution(src, dest):
    if src == dest:
        return 0
    src, dest = divmod(src, 8), divmod(dest, 8)
    queue = deque([(0, src)])
    not_seen = {(x, y) for x in range(8) for y in range(8)} - {src}
    seen = set(queue)
    while queue:
        dist, (this_x, this_y) = queue.popleft()
        for dx, dy in DELTA:
            next = (this_x + dx, this_y + dy)
            if next == dest:
                return dist + 1
            elif next in not_seen:
                not_seen.remove(next)
                queue.append((dist + 1, next))


def solution2(x, y):
    return (x + y) * (x + y - 1) // 2 - (y - 1)

def solution3(items):
    items.sort(reverse=True)
    for digits in range(len(items), 0, -1):
        values = [x for x in itertools.combinations(items, digits) if sum(x) % 3 == 0]
        if values:
            result = max(values)
            return int(''.join(str(i) for i in result))
    return 0

def solution4(items, result):
    accum = {}
    accum[0] = -1
    total = 0
    for index, value in enumerate(items):
        total += value
        if total - result in accum:
            return accum[total - result] + 1, index
        accum[total] = index
    return [-1, -1]

def solution5(area):
    result = []
    while area > 0:
        result.append(int(math.sqrt(area)) ** 2)
        area -= result[-1]
    return result

def prime_generator():
    for x in [2, 3, 5, 7]:
        yield x
    factor_sequence = prime_generator()
    next(factor_sequence)  # we don't need the 2, since we're only looking at odd numbers
    factors = [next(factor_sequence)]  # i.e. [3]
    while True:
        # The last element we pulled from factor_sequence was factors[-1]
        # We have generated all primes through factor[-1] ** 2 (which can't be a prime).
        next_factor = next(factor_sequence)
        # Let's look at all oee numbers through next_factor**2 (exclusive).
        # All composites must have at least one factor smaller than next_factor.
        for value in range((factors[-1] ** 2) + 2, next_factor ** 2, 2):
            if all(value % factor for factor in factors):
                yield value
        factors.append(next_factor)

def solution7(n):
    length = 0
    result = collections.deque()
    for prime in prime_generator():
        result.append(str(prime))
        length += len(result[-1])
        if length > n + 5:
            break
    while n >= len(result[0]):
        n -= len(result.popleft())
    return ''.join(result)[n:n+5]


def solution8(list, n):
    c = collections.Counter(list)
    extras = {key for key, value in c.items() if value > n}
    return [x for x in list if x not in extras]


if __name__ == '__main__':
    print(solution8([1, 2, 2, 3, 3, 3, 4, 5, 5], 1))   # 02192
