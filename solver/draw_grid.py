import itertools
from collections.abc import Sequence, Callable
from typing import Any, cast, Optional

from matplotlib import pyplot as plt, patches
from matplotlib.axes import Axes

from .clue_types import Location


def draw_grid(*, max_row: int, max_column: int,
              clued_locations: set[Location],
              location_to_entry: dict[Location, str],
              location_to_clue_numbers: dict[Location, Sequence[str]] = {},
              top_bars: set[Location] = set(),
              left_bars:  set[Location] = set(),
              shading: dict[Location, str] = {},
              rotation: dict[Location, str] = {},
              circles: set[Location] = set(),
              subtext: Optional[str] = None,
              font_multiplier: float = 1.0,
              blacken_unused: bool = True,
              grid_drawer: Callable[[...], None] = None,
              extra: Callable[[...], None] = None,
              **args: Any) -> None:

    _axes = args.get('axes')
    if _axes:
        axes = cast(Axes, _axes)
    else:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)

    # set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([1, max_column, max_row, 1])
    axes.axis('equal')
    axes.axis('off')

    # Fill in the shaded squares
    for row, column in itertools.product(range(1, max_row), range(1, max_column)):
        if (row, column) in shading:
            color = shading[row, column]
            axes.add_patch(patches.Rectangle((column, row), 1, 1,
                                             facecolor=color, linewidth=0))
        elif (row, column) not in clued_locations:
            if blacken_unused:
                axes.add_patch(patches.Rectangle((column, row), 1, 1,
                                                 facecolor='black', linewidth=0))

    if grid_drawer is None:
        for row, column in itertools.product(range(1, max_row + 1), range(1, max_column + 1)):
            this_exists = (row, column) in clued_locations
            left_exists = (row, column - 1) in clued_locations
            above_exists = (row - 1, column) in clued_locations
            if this_exists or left_exists:
                width = 5 if this_exists != left_exists or (row, column) in left_bars else None
                axes.plot([column, column], [row, row + 1], 'black', linewidth=width)
            if this_exists or above_exists:
                width = 5 if this_exists != above_exists or (row, column) in top_bars else None
                axes.plot([column, column + 1], [row, row], 'black', linewidth=width)

            if (row, column) in shading:
                color = shading[row, column]
                axes.add_patch(patches.Rectangle((column, row), 1, 1, facecolor=color, linewidth=0))
    else:
        grid_drawer(plt, axes)

    for row, column in circles:
        circle = plt.Circle((column + .5, row + .5), radius=.4, linewidth=2, fill=False, facecolor='black')
        axes.add_patch(circle)

    points_per_data = 60 * font_multiplier

    # Fill in the values
    for (row, column), entry in location_to_entry.items():
        axes.text(column + 1 / 2, row + 1 / 2, entry,
                  fontsize=points_per_data/2, fontweight='bold', fontfamily="sans-serif",
                  verticalalignment='center', horizontalalignment='center',
                  rotation=rotation.get((row, column), 0))

    if subtext is not None:
        axes.text((max_column + 1) / 2, max_row + .5, subtext,
                  fontsize=points_per_data / 2, fontweight='bold', fontfamily="sans-serif",
                  verticalalignment='center', horizontalalignment='center')

    # Fill in the clue numbers
    for (row, column), clue_numbers in location_to_clue_numbers.items():
        font_info = dict(fontsize=points_per_data / 4, fontfamily="sans-serif")
        for index, text in enumerate(clue_numbers):
            if index == 0:
                axes.text(column + .05, row + .05, text,
                          verticalalignment='top', horizontalalignment='left', **font_info)
            elif index == 1:
                axes.text(column + .95, row + .05, text,
                          verticalalignment='top', horizontalalignment='right', **font_info)
            elif index == 2:
                axes.text(column + .05, row + .95, text,
                          verticalalignment='bottom', horizontalalignment='left', **font_info)
            elif index == 3:
                axes.text(column + .95, row + .95, text,
                          verticalalignment='bottom', horizontalalignment='right', **font_info)

    if extra:
        extra(plt, axes)
    if not _axes:
        plt.show()
