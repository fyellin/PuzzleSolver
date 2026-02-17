import itertools

from solver import DancingLinks
from solver.draw_grid import draw_grid

ACROSS = [
  "POTATOPIT", "DHARMSHALA", "ERRORIST", "CREPEHANGING",
  "ANOESTRI", "TENTPEG", "DITHYRAMB", "PTERODACTYL",
  "IRAIMBILANJA", "CAFESAULAIT", "GENERIC", "DISTEMPERS"
]

ACROSS_LENGTHS = [9, 10, 8, 12, 8, 7, 9, 11, 12, 11, 7, 10]

DOWNS = ["ALTERCATE", "ANTITRAGI", "CARPENTRIES", "PRECIPICED",
         "RESTHOME", "SIMPAIS", "SIRGANG", "TAILBACK",
         "THINGAMYJIGS", "THREADBARE", "THREELEAFED", "THUNDERPLUMP"]

DOWN_LENGTHS = [9, 9, 11, 10, 8, 7, 7, 8, 12, 10, 11, 12]


class Solver:
    def __init__(self):
        for word, length in zip(ACROSS, ACROSS_LENGTHS):
            assert len(word) == length, f"{word} has wrong length {length}"
        for word, length in zip(DOWNS, DOWN_LENGTHS):
            assert len(word) == length, f"{word} has wrong length {length}"
        self.results = set()

    def handle_solution(self, solution):
        locations = {}
        for (aa, is_across, word, indices) in solution:
            for bb, letter in zip(indices, word):
                row, col = (aa, bb) if is_across else (bb, aa)
                if (row, col) in locations:
                    assert locations[row, col] == letter
                locations[row, col] = letter
        assert len(locations) == 144
        result = ''.join(locations[row, col]
                         for row in range(1, 13) for col in range(1, 13))
        self.results.add(result)

    def solve(self):
        constraints = {}
        optionals = {f'r{r}c{c}' for r in range(1, 13) for c in range(1, 13)}
        for word_list in (ACROSS, DOWNS):
            is_across = word_list is ACROSS
            for word_index, word in enumerate(word_list, start=1):
                for indices in itertools.combinations(range(1, 13), len(word)):
                    for aa in [word_index] if is_across else range(1, 13):
                        constraint = [word, f'{"A" if is_across else "D"}-{aa}']
                        for bb, letter in zip(indices, word):
                            name = f'r{aa}c{bb}' if is_across else f'r{bb}c{aa}'
                            constraint.append((name, letter))
                        # for bb in range(1, 13):
                        #     if bb not in indices:
                        #         constraint.append(f'EMPTY-{to_rc(aa, bb)}')
                        constraints[aa, is_across, word, indices] = constraint

        solver = DancingLinks(constraints, optional_constraints=optionals,
                              row_printer=self.handle_solution)
        solver.solve(debug=0)
        assert len(self.results) == 1
        self.draw_grid(self.results.pop())

    def draw_grid(self, solution=None):
        # solution = solution or "POTCATOTPITTRDHARMSHALHAEARRORIULSITCREPEHANGINGANOESRMDTRGIITENTEPEEGALDILTHAYRRAMBPTERODAPCTYLIRAIMBILANJACAFESASULAITEGENERIMTGGCDIDSTEMPERSK"
        locations = dict(zip(itertools.product(range(1, 13), repeat=2), solution))
        clue_numbers = {(i, 1): [i] for i in range(1, 13)}
        draw_grid(max_row=13, max_column=13, location_to_entry=locations,
                  location_to_clue_numbers=clue_numbers, font_multiplier=.6)


if __name__ == '__main__':
    Solver().solve()
