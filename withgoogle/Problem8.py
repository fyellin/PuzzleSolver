from __future__ import division

import functools
import itertools
from fractions import Fraction

try:
    from fractions import gcd
except:
    from math import gcd


def solution(steps):
    return sum(steps_with_min_height(steps, x) for x in range(1, steps + 1)) - 1

cache = {}

def steps_with_min_height(steps, min_height):
    temp = cache.get((steps, min_height))
    if temp is not None:
        return temp
    result = cache[(steps, min_height)] = _steps_with_min_height(steps, min_height)
    return result


def _steps_with_min_height(steps, first):
    assert steps > 0
    if steps < first:
        return 0
    if steps == first:
        return 1
    result = sum(steps_with_min_height(steps - first, x) for x in range(first + 1, steps - first + 1))
    return result


import base64
from itertools import cycle

message = "HV4WGQ8KCxUKQkxWSUkBCwANGE5CRl4GAwAFCwceEAlLSVRGXgAfGAwLCxwBS0BJSQMfAwMeHR1B WV9MSwAABQsACAULAgNeSUxLCA0OEAAaCQQLCA1CTFZJSRMXCQMPAgsCXklMSxsPBBsMGB9OTlxZ Qh8NDwtBVUVLCgYBQVlfTEseBwhYQhE="
key = bytes("fyellin", "utf8")
print(bytes(a ^ b for a, b in zip(base64.b64decode(message), cycle(key))))


def foo():
    answers = set()
    for items in itertools.product(('a', 'b', 'c'), repeat=7):
        aa = tuple(index for index, item in enumerate(items) if item == 'a')
        bb = tuple(index for index, item in enumerate(items) if item == 'b')
        cc = tuple(index for index, item in enumerate(items) if item == 'c')
        answers.add(tuple(sorted((aa, bb , cc))))
    for i in sorted(answers):
        print(i)
    print(len(answers))

if __name__ == '__main__':
    foo()
