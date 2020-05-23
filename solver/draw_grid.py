import itertools
from typing import Set, Dict, Any, cast

from matplotlib import pyplot as plt, patches
from matplotlib.axes import Axes
from matplotlib.transforms import Bbox

from .clue_types import Location


def draw_grid(max_row: int, max_column: int, clued_locations: Set[Location],
              location_to_entry: Dict[Location, str],
              location_to_clue_number: Dict[Location, str],
              top_bars: Set[Location],
              left_bars: Set[Location],
              **more_args: Dict[str, Any]) -> None:
    _axes = more_args.get('axes')
    if _axes:
        axes = cast(Axes, _axes)
    else:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)

    shading = cast(Dict[Location, str], more_args.get('shading', {}))
    rotation = cast(Dict[Location, int], more_args.get('rotations', {}))

    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([1, max_column, max_row, 1])
    axes.axis('equal')
    axes.axis('off')

    # Fill in the shaded squares
    for row, column in itertools.product(range(1, max_row), range(1, max_column)):
        if (row, column) in shading:
            color = shading[row, column]
            axes.add_patch(patches.Rectangle((column, row), 1, 1, facecolor=color, linewidth=0))
        # elif (row, column) not in clued_locations:
        #     axes.add_patch(patches.Rectangle((column, row), 1, 1, facecolor='black', linewidth=0))

    for row, column in itertools.product(range(1, max_row + 1), range(1, max_column + 1)):
        this_exists = (row, column) in location_to_entry
        left_exists = (row, column - 1) in location_to_entry
        above_exists = (row - 1, column) in location_to_entry
        if this_exists or left_exists:
            width = 5 if this_exists != left_exists or (row, column) in left_bars else None
            axes.plot([column, column], [row, row + 1], 'black', linewidth=width)
        if this_exists or above_exists:
            width = 5 if this_exists != above_exists or (row, column) in top_bars else None
            axes.plot([column, column + 1], [row, row], 'black', linewidth=width)

        if (row, column) in shading:
            color = shading[row, column]
            axes.add_patch(patches.Rectangle((column, row), 1, 1, facecolor=color, linewidth=0))

    scaled_box = Bbox.unit().transformed(axes.transData - axes.figure.dpi_scale_trans)
    inches_per_data = min(abs(scaled_box.width), abs(scaled_box.height))
    points_per_data = 72 * inches_per_data

    # Fill in the values
    for (row, column), entry in location_to_entry.items():
        axes.text(column + 1 / 2, row + 1 / 2, entry,
                  fontsize=points_per_data/2, fontweight='bold', fontfamily="sans-serif",
                  verticalalignment='center', horizontalalignment='center',
                  rotation=rotation.get((row, column), 0))


    # Fill in the clue numbers
    for (row, column), clue_number in location_to_clue_number.items():
        text = str(clue_number)
        split_text = text.split(', ', 1)
        if len(split_text) == 2:
            text, remainder = split_text
        else:
            remainder = None
        axes.text(column + 1 / 20, row + 1 / 20, text,
                  fontsize=points_per_data/4, fontfamily="sans-serif",
                  verticalalignment='top', horizontalalignment='left')
        if remainder:
            axes.text(column + 19 / 20, row + 1 / 20, remainder,
                      fontsize=points_per_data / 4, fontfamily="sans-serif",
                      verticalalignment='top', horizontalalignment='right')

    if not _axes:
        plt.show()
