from __future__ import division

def solution(h, query):
    high = (1 << h) - 1
    return [get_parent(value, 1, high, -1) for value in query]


def get_parent(value, low, high, parent):
    while True:
        assert low <= value <= high
        if value == high:
            return parent
        lowest_of_top = (low + high) // 2
        if value < lowest_of_top:
            low, high, parent = low, lowest_of_top - 1, high
        else:
            low, high, parent = lowest_of_top, high - 1, high



if __name__ == '__main__':
    print(solution(3, [7, 3, 5, 1]))
    print(solution(5, [19, 14, 28]))
    print("-1, 7, 6, 3")
    print("21, 15, 29")
