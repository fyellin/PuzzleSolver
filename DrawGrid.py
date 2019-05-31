import itertools
from typing import Set, Dict, Tuple

from matplotlib import pyplot as plt, patches

Location = Tuple[int, int]


def draw_grid(max_row: int, max_column: int, clued_locations: Set[Location],
              location_to_entry: Dict[Location, str],
              location_to_clue_number: Dict[Location, str],
              top_bars: Set[Location],
              left_bars: Set[Location]) -> None:
    plt.figure(figsize=(max_column * .8, max_row * .8), dpi=100)
    axis = plt.gca()
    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    plt.axis([1, max_column, max_row, 1])
    plt.axis('equal')
    plt.axis('off')

    # Draw the bold outline
    plt.plot([1, max_column, max_column, 1, 1], [1, 1, max_row, max_row, 1], linewidth=5, color='black')

    # Draw the interior grid
    for row in range(2, max_row):
        # horizontal lines
        plt.plot([1, max_column], [row, row], 'black')
    for column in range(2, max_column):
        # vertical lines
        plt.plot([column, column], [1, max_row], 'black')

    # Fill in the black squares
    for row, column in itertools.product(range(1, max_row), range(1, max_column)):
        if (row, column) not in clued_locations:
            axis.add_patch(patches.Rectangle((column, row), 1, 1, facecolor='black'))

    # Fill in the values
    for (row, column), entry in location_to_entry.items():
        axis.text(column + 1 / 2, row + 1 / 2, entry, fontsize=25, fontweight='bold',
                  verticalalignment='center', horizontalalignment='center')

    # Fill in the clue numbers
    for (row, column), clue_number in location_to_clue_number.items():
        axis.text(column + 1 / 20, row + 1 / 20, str(clue_number), fontsize=12,
                  verticalalignment='top', horizontalalignment='left')

    # Draw thick bars to left or top, as necessary
    for row, column in left_bars:
        plt.plot([column, column], [row, row + 1], 'black', linewidth=5)
    for row, column in top_bars:
        plt.plot([column, column + 1], [row, row], 'black', linewidth=5)

    plt.show()
