import itertools
from typing import Set, Dict, Tuple, Optional

from matplotlib import pyplot as plt, patches
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox

Location = Tuple[int, int]


def draw_grid(max_row: int, max_column: int, clued_locations: Set[Location],
              location_to_entry: Dict[Location, str],
              location_to_clue_number: Dict[Location, str],
              top_bars: Set[Location],
              left_bars: Set[Location],
              axes: Optional[Axes] = None) -> None:

    if axes:
        ax = axes
    else:
        _, ax = plt.subplots(1, 1, figsize=(8, 11), dpi=100)

    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    ax.axis([1, max_column, max_row, 1])
    ax.axis('equal')
    ax.axis('off')

    # Draw the bold outline
    ax.plot([1, max_column, max_column, 1, 1], [1, 1, max_row, max_row, 1], linewidth=5, color='black')

    # Draw the interior grid
    for row in range(2, max_row):
        # horizontal lines
        ax.plot([1, max_column], [row, row], 'black')
    for column in range(2, max_column):
        # vertical lines
        ax.plot([column, column], [1, max_row], 'black')

    # Fill in the black squares
    for row, column in itertools.product(range(1, max_row), range(1, max_column)):
        if (row, column) not in clued_locations:
            ax.add_patch(patches.Rectangle((column, row), 1, 1, facecolor='black', linewidth=0))

    # Draw thick bars to left or top, as necessary
    for row, column in left_bars:
        ax.plot([column, column], [row, row + 1], 'black', linewidth=5)
    for row, column in top_bars:
        ax.plot([column, column + 1], [row, row], 'black', linewidth=5)

    # Draw thick bars to left or top, as necessary
    for row, column in left_bars:
        ax.plot([column, column], [row, row + 1], 'black', linewidth=5)
    for row, column in top_bars:
        ax.plot([column, column + 1], [row, row], 'black', linewidth=5)

    scaled_box = Bbox.unit().transformed(ax.transData - ax.figure.dpi_scale_trans)
    inches_per_data = min(abs(scaled_box.width), abs(scaled_box.height))
    points_per_data = 72 * inches_per_data

    # Fill in the values
    for (row, column), entry in location_to_entry.items():
        ax.text(column + 1 / 2, row + 1 / 2, entry, fontsize=points_per_data/2, fontweight='bold',
                verticalalignment='center', horizontalalignment='center')

    # Fill in the clue numbers
    for (row, column), clue_number in location_to_clue_number.items():
        ax.text(column + 1 / 20, row + 1 / 20, str(clue_number), fontsize=points_per_data/4,
                verticalalignment='top', horizontalalignment='left')

    if not axes:
        plt.show()
