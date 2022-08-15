from __future__ import division

import functools
from fractions import Fraction

try:
    from fractions import gcd
except:
    from math import gcd


def solution(input):
    length = len(input)
    outputs = []
    transitions = {}
    for row, line in enumerate(input):
        total = sum(line)
        if total == 0:
            outputs.append(row)
        else:
            transitions[row] = {column: Fraction(value, total) for column, value in enumerate(line)}
            assert sum(transitions[row].values()) == 1

    if 0 in outputs:
        return [1] + ([0] * (length - 1)) + [1]

    for row, transition in transitions.items():
        if transition[row] != 0:
            # Remove the item, and normalize everything else in the row
            new_total = 1 - transition[row]
            transition[row] = 0
            for i in range(length):
                transition[i] /= new_total
            assert sum(transition.values()) == 1
        for row2, transition2 in transitions.items():
            temp = transition2[row]
            if temp != 0:
                assert sum(transition2.values()) == 1
                transition2[row] = 0
                for i in range(length):
                    transition2[i] += temp * transition[i]
                assert sum(transition2.values()) == 1

    values = [transitions[0][i] for i in outputs]
    denominator = functools.reduce(lcd, (x.denominator for x in values), 1)
    values = [int(denominator * value) for value in values]
    values.append(denominator)
    return values


def lcd(x, y):
    return x * y // gcd(x, y)


if __name__ == '__main__':
    result1 = solution([[0, 2, 1, 0, 0], [0, 0, 0, 3, 4], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]])
    print(result1, result1 == [7, 6, 8, 21])

    result2 = solution(
       [[0, 1, 0, 0, 0, 1], [4, 0, 0, 3, 2, 0], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0],
           [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]])
    print(result2, result2 == [0, 3, 2, 9, 14])
