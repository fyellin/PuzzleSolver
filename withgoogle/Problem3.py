from collections import defaultdict, deque
from itertools import tee

def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def solution(entrances, exits, path):
    infinity = float('inf')
    flow = defaultdict(int)
    capacity = defaultdict(int)
    for row, values in enumerate(path):
        for column, value in enumerate(values):
            capacity[(row, column)] = value
    source = 'S'
    for s in entrances:
        capacity[(source, s)] = infinity
    sink = 'T'
    for t in exits:
        capacity[(t, sink)] = infinity
    nodes = set(range(len(path))).union({source, sink})

    def get_shortest_path():
        queue = deque([[source]])
        seen = {source}
        while queue:
            path = queue.popleft()
            tail = path[-1]
            for node in nodes:
                if node not in seen and capacity[tail, node] > flow[tail, node]:
                    seen.add(node)
                    new_path = path + [node]
                    if node == sink:
                        return list(pairwise(new_path))
                    queue.append(new_path)
        return None

    result = 0
    while True:
        path = get_shortest_path()
        if not path:
            return result
        min_flow = min(capacity[s, d] - flow[s, d] for s, d in path)
        result += min_flow
        for s, d in path:
            flow[s, d] += min_flow
            flow[d, s] -= min_flow



if __name__ == '__main__':
    print(solution([0], [3], [[0, 7, 0, 0], [0, 0, 6, 0], [0, 0, 0, 8], [9, 0, 0, 0]]))  #6
    print(solution([0, 1], [4, 5],
                  [[0, 0, 4, 6, 0, 0], [0, 0, 5, 2, 0, 0], [0, 0, 0, 0, 4, 4],
                   [0, 0, 0, 0, 6, 6], [0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0]]))  #16
