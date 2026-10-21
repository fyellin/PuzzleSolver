import itertools
from collections import defaultdict
from collections.abc import Hashable, Sequence

import more_itertools
from more_itertools import is_prime
from rich import print as pprint
from rich.markup import escape

from misc.UnionFind import UnionFind
from solver import (
    Clue,
    DancingLinksSolver,
    DLConstraint,
    KnownClueDict,
)

ACROSS = "84/417/116111/C/51114/81111/11118/41115/C/1111611/714/48"


class Harpers(DancingLinksSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()
        solver.show_final()

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues)
        self.symmetries = self.join_symmetries()
        self.results = defaultdict(set)

    def get_clues(self):
        across = ACROSS
        downs = '/'.join(reversed(across.split('/')))
        from solver import Clues
        return Clues.clues_from_clue_sizes(across, downs)

    def join_symmetries(self) -> dict[Clue, set[Clue]]:
        uf = UnionFind()
        clue_start_set = {(clue.base_location, clue.length, clue.is_across): clue
                          for clue in self.clue_list}
        for clue in self.clue_list:
            # The location in this clue that matches the start of its 90° rotation
            row, column = clue.location(0 if clue.is_across else clue.length - 1)
            # The presumed start location of the clue located 90° clockwise.
            row2, column2 = column, 13 - row
            next_clue = clue_start_set[(row2, column2), clue.length, not clue.is_across]
            uf.union(clue, next_clue)
        result = defaultdict(list)
        for clue1, clue2 in itertools.product(self.clue_list, repeat=2):
            if uf.find(clue1) == uf.find(clue2):
                result[clue1].append(clue2)
        return result

    def update_constraints(self, constraints: dict[Hashable, list[DLConstraint]],
                           optional_constraints: set[str],
                           bounds: dict[str, tuple[int, int]]) -> None:
        def doit(name, *values):
            clues = self.symmetries[self.clue_named(name)]
            for value in values:
                assert len(value) == clues[0].length
            for clue in clues:
                for value in values:
                    constraints[clue, value] = [
                        f'clue_{clue.name}',
                        f'value={value}',
                        *clue.dancing_links_rc_constraints(value),
                    ]
                if len(values) < 4:
                    optional_constraints.add(f'clue_{clue.name}')

        doit('1a', 'ASSAGAIS')
        doit('7a', 'IAMB')
        doit('10a', 'EVEN')
        doit('11a', 'AGINNER')
        doit("12a", "SKIING")
        doit('14a', 'MOUNTAINEERS', 'INSECTIVORES', 'ACKNOWLEDGER', 'QUADRAPHONIC')
        doit('15a', 'SIGNS', 'KRONA')
        doit('19a', 'IGNITRON', 'ANYWHERE', 'REDRAFTS', 'ADONISES')

    def show_solutionx(self, known_clues: KnownClueDict) -> None:
        for clue, value in known_clues.items():
            self.results[value].add(clue.name)

    def show_final(self):
        return
        for value, clues in self.results.items():
            print(value, clues)


if __name__ == '__main__':
    Harpers.run()
