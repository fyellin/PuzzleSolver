from typing import Generic

from misc.Tester import Node


class UnionFind(Generic[Node]):
    parent: dict[Node, Node]
    rank: dict[Node, int]

    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x: Node):
        parent = self.parent
        parent.setdefault(x, x)
        root = x
        while (nextNode := parent[root]) != root:
            root = nextNode
        while (nextNode := parent[x]) != root:
            x, parent[x] = nextNode, root
        return root

    def union(self, x: Node, y: Node):
        x = self.find(x)
        y = self.find(y)
        if x != y:
            rank_x = self.rank.setdefault(x, 1)
            rank_y = self.rank.setdefault(y, 1)
            if rank_x > rank_y:
                # We dont' swap rank_x and rank_y because after this,
                # we only care if they're equal
                x, y = y, x
            self.parent[x] = y
            if rank_x == rank_y:
                self.ranky = rank_y + 1
