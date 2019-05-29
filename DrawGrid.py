import itertools
from typing import Set, Dict, Tuple

from matplotlib import pyplot as plt, patches

Location = Tuple[int, int]


def draw_grid(max_row: int, max_column: int, clued_locations: Set[Location],
              location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
              top_bars: Set[Location], left_bars: Set[Location]) -> None:
    plt.figure(figsize=(max_column * .8, max_row * .8), dpi=100)
    axis = plt.gca()
    # 1,1 is the top-left corner.  max_column, max_row is the bottom right.
    plt.axis([1, max_column, max_row, 1])
    plt.axis('equal')
    plt.axis('off')
    # Draw the bold outline
    axis.add_patch(
        patches.Rectangle((1, 1), max_column - 1, max_row - 1, linewidth=5, color='black', fill=False))
    # Draw the interior grid
    for row in range(2, max_row):
        plt.plot([1, max_column], [row, row], 'black')
    for column in range(2, max_column):
        plt.plot([column, column], [1, max_row], 'black')
    # draw the answers and black squares
    for location in itertools.product(range(1, max_row), range(1, max_column)):
        row, column = location
        if location in clued_locations:
            entry = location_to_entry.get(location, None)
            if entry:
                # Print the entry centered in the square
                axis.text(column + 1 / 2, row + 1 / 2, entry, fontsize=25, fontweight='bold',
                          verticalalignment='center', horizontalalignment='center')
            clue_number = location_to_clue_number.get(location, None)
            if clue_number:
                # Print the clue number using a smaller font in the top left
                axis.text(column + 1 / 20, row + 1 / 20, str(clue_number), fontsize=12,
                          verticalalignment='top', horizontalalignment='left')

        else:
            # This isn't part of a clue? Draw a black rectangle.
            axis.add_patch(patches.Rectangle((column, row), 1, 1, facecolor='black'))
    # Draw thick bars to left or top, as necessary
    for row, column in left_bars:
        plt.plot([column, column], [row, row + 1], 'black', linewidth=5)
    for row, column in top_bars:
        plt.plot([column, column + 1], [row, row], 'black', linewidth=5)

    plt.show()
