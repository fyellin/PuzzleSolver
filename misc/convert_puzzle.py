import argparse
import itertools
import os
import sys
import tempfile
from contextlib import ExitStack
from typing import Optional, List, Any, Set, Tuple

import cv2
import numpy as np


def convert_grid(input_name: str, **args) -> None:
    if input_name.upper().endswith(".PDF"):
        with tempfile.TemporaryDirectory() as directoryName:
            filename = os.path.join(directoryName, "temp.jpg")
            os.system(f"/usr/bin/sips -s format jpeg -s formatOptions best \"{input_name}\" -o {filename} > /dev/null")
            img = cv2.imread(filename)
    else:
        img = cv2.imread(input_name)

    # convert the puzzle into a format that findContours can use.  This is magic to me.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    thresh2 = cv2.bitwise_not(thresh)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    # Look at the contours whose approximating polygon is a 4-sided polygon (hopefully, a rectangle), and take the one
    # that has the largest area.  This should be the entire puzzle grid.
    # This is the contour representing the entire puzzle
    _, puzzle_contour_index = max((cv2.contourArea(contour), index) for index, contour in enumerate(contours)
                                  for approx in [cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)]
                                  if len(approx) == 4)

    # The contours that are immediate descendants of the puzzle_contour index are the white squares.
    bounding_rectangles = []
    used_contours = []
    for contour, (_next, _prev, _child, parent), i in zip(contours, hierarchy[0], itertools.count()):
        if parent == puzzle_contour_index:
            x, y, w, h = rectangle = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            white_count = cv2.countNonZero(thresh2[y:y + h, x:x + w])
            if white_count >= .75 * area:
                bounding_rectangles.append(rectangle)
                used_contours.append(contour)
            else:
                print(f"Strangeness at {rectangle}")

    # Collect up the <x, y> components and the <width, height> components into numpy arrays
    contours_x_y_w_h = np.array(bounding_rectangles)
    puzzle_x, puzzle_y = np.min(contours_x_y_w_h[..., 0:2], axis=0)
    puzzle_w, puzzle_h = np.max(contours_x_y_w_h[..., 0:2] + contours_x_y_w_h[..., 2:4], axis=0) - [puzzle_x, puzzle_y]

    square_width = square_height = 0.0
    row_heights = column_widths = 0.0
    num_columns = num_rows = 1
    column_indices = row_indices = np.array(())
    for num_columns in itertools.count(2):
        square_width = puzzle_w / num_columns
        approximate_column_indices = (contours_x_y_w_h[..., 0] - puzzle_x) / square_width
        approximate_column_widths = (contours_x_y_w_h[..., 2] / square_width)
        column_indices = np.round(approximate_column_indices).astype(int)
        column_widths = np.round(approximate_column_widths).astype(int)
        delta = np.max(np.abs(column_indices - approximate_column_indices))
        if delta < .20:
            break

    for num_rows in itertools.count(2):
        square_height = puzzle_h / num_rows
        approximate_row_indices = (contours_x_y_w_h[..., 1] - puzzle_y) / square_height
        approximate_row_heights = (contours_x_y_w_h[..., 3] / square_height)
        row_indices = np.round(approximate_row_indices).astype(int)
        row_heights = np.round(approximate_row_heights).astype(int)
        delta = np.max(np.abs(row_indices - approximate_row_indices))
        if delta < .20:
            break

    indices = set()

    # clone = img.copy()
    for contour, row, column, height, width \
            in zip(used_contours, row_indices, column_indices, row_heights, column_widths):
        if width == height == 1:
            indices.add((row, column))
        else:
            # clone = cv2.drawContours(clone, [contour], -1, (255, 0, 0), 3)
            for dr, dc in itertools.product(range(height), range(width)):
                cx = puzzle_x + (column + dc + .5) * square_width
                cy = puzzle_y + (row + dr + .5) * square_height
                if cv2.pointPolygonTest(contour, (cx, cy), False) > 0:
                    indices.add((row + dr, column + dc))
                else:
                    print(f"Not adding({row + dr}, {column + dc})")

    # cv2.imwrite("/tmp/foo.jpg", clone)
    # os.system(f"/usr/bin/open /tmp/foo.jpg > /dev/null")
    indices = np.array(sorted(indices))

    # There is some code that I removed that handles the image being rotated. I deleted when I totally re-did
    # this code.
    # https://stackoverflow.com/questions/16975556/crossword-digitization-using-image-processing?rq=1

    if args['puzzle']:
        handle_nyt_puzzle(num_columns, num_rows, indices, **args)
    else:
        contours_x_y_w_h -= [puzzle_x, puzzle_y, 0, 0]
        handle_harpers_puzzle(num_columns, num_rows, indices, contours_x_y_w_h, **args)


def handle_harpers_puzzle(num_columns: int, num_rows: int, indices: np.ndarray, contours_x_y_w_h: np.ndarray,
                          **_args: Any) -> None:
    print(f"Grid is {num_rows} rows by {num_columns} columns.")
    print(f"There are {num_rows * num_columns - len(indices)} black squares.")
    squares_x_y_x2_y2 = np.zeros((num_rows, num_columns, 4), dtype=contours_x_y_w_h.dtype)
    for (row, column), (x, y, w, h) in zip(indices, contours_x_y_w_h):
        squares_x_y_x2_y2[row, column] = [x, y, x + w, y + h]

    min_left_per_column = np.min(squares_x_y_x2_y2[:, :, 0], axis=0)
    max_right_per_column = np.max(squares_x_y_x2_y2[:, :, 2], axis=0)
    min_top_per_row = np.min(squares_x_y_x2_y2[:, :, 1], axis=1)
    max_bottom_per_row = np.max(squares_x_y_x2_y2[:, :, 3], axis=1)

    left_inset = squares_x_y_x2_y2[..., 0] - min_left_per_column
    right_inset = max_right_per_column - squares_x_y_x2_y2[..., 2]
    top_inset = squares_x_y_x2_y2[..., 1] - min_top_per_row[..., None]
    bottom_inset = max_bottom_per_row[..., None] - squares_x_y_x2_y2[..., 3]

    right_border = right_inset[:, :-1] + left_inset[:, 1:]
    bottom_border = bottom_inset[:-1] + top_inset[1:]
    right_bars = set(zip(*np.where(right_border > 5)))
    bottom_bars = set(zip(*np.where(bottom_border > 5)))
    for row, column in itertools.product(range(num_rows, num_columns)):
        is_left = column == 0 or (row, column - 1) in right_bars
        is_right = column == num_columns - 1 or (row, column) in right_bars
        is_top = row == 0 or (row - 1, column) in bottom_bars
        is_bottom = row == num_rows - 1 or (row, column) in bottom_bars
        is_across_clue = is_left and not is_right
        is_down_clue = is_top and not is_bottom

    is_symmetric = all((num_rows - row - 1, num_columns - column - 2) in right_bars
                       for (row, column) in right_bars) \
               and all((num_rows - row - 2, num_columns - column - 1) in bottom_bars
                       for (row, column) in bottom_bars)
    print(f"The grid is {'' if is_symmetric else 'not '}180º symmetric")


def handle_nyt_puzzle(no_columns, no_rows, indices,
                      *, copyright: str, title: str, author: str,
                      output_file_name: str,
                      clue_file: str, **_args: Any) -> None:
    # squares = {(row, column) for (column, row) in indices}
    squares = {(row, column) for (row, column) in indices}
    print(f"Grid is {no_rows} rows by {no_columns} columns.")
    print(f"There are {no_rows * no_columns - len(squares)} black squares.")
    is_symmetric = all(((row, column) in squares) == ((no_rows - row - 1, no_columns - column - 1) in squares)
                       for row in range(no_rows) for column in range(no_columns))
    print(f"The grid is {'' if is_symmetric else 'not '}180º symmetric")
    down_clues = {(row, column) for (row, column) in squares if (row - 1, column) not in squares}
    across_clues = {(row, column) for (row, column) in squares if (row, column - 1) not in squares}
    print(f"There are {len(across_clues)} across clues and {len(down_clues)} down clues.")
    if clue_file:
        clues = _parse_clue_file(clue_file, across_clues, down_clues)
    else:
        clues = ["#"] * (len(across_clues) + len(down_clues))
    with ExitStack() as stack:
        file = stack.enter_context(open(output_file_name, "w", encoding="iso-8859-1")) \
            if output_file_name else sys.stdout
        file.write("<ACROSS PUZZLE>\n")
        file.write(f"<TITLE>\n{title}\n")
        file.write(f"<AUTHOR>\n{author}\n")
        file.write(f"<COPYRIGHT>\n{copyright}\n")
        # Documentation doesn't say which goes first.  But I verified experimentally.
        file.write(f"<SIZE>\n{no_columns}x{no_rows}\n")
        file.write("<GRID>\n")
        for row in range(no_rows):
            for column in range(no_columns):
                file.write('X' if (row, column) in squares else '.')
            file.write("\n")
        file.write("<ACROSS>\n")
        for _ in range(len(across_clues)):
            file.write(clues.pop(0) + "\n")
        file.write("<DOWN>\n")
        for _ in range(len(down_clues)):
            file.write(clues.pop(0) + "\n")
        file.write("<NOTEPAD>\n")
        assert len(clues) == 0


def _parse_clue_file(clue_file: str, across_clues: Set[Tuple[int, int]], down_clues: Set[Tuple[int, int]]) -> List[str]:
    clue_number_to_location = list(enumerate(sorted(across_clues.union(down_clues)), start=1))
    result = []
    with open(clue_file) as file:
        lines = iter(file)
        for these_clues, clue_type in ((across_clues, 'A'), (down_clues, 'D')):
            number_and_location = [(i, location) for i, location in clue_number_to_location if location in these_clues]
            for clue_number, location in number_and_location:
                line = next(lines).strip()
                assert line.strip() == str(clue_number), f'For Clue {clue_number} read {line.strip()} from file'
                result.append(next(lines).strip())
    return result

def main(arguments: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description='Process log files.')
    parser.add_argument(action="store", dest="input_file_name", help="file to convert")
    parser.add_argument('--output', '-o', action='store', dest='output_file_name', help="outupt file name")
    parser.add_argument('--title', action='store', dest='title', help="title of puzzle", default="")
    parser.add_argument('--author', action='store', dest='author', help="author of puzzle", default="")
    parser.add_argument('--copyright', action='store', dest='copyright', help="copyright notice", default="")
    parser.add_argument('--puzzle', '-p', action='store_true', dest='puzzle', default=False)
    parser.add_argument('--clues', action='store', dest='clue_file', default='')
    args = parser.parse_args(arguments)
    if not args.output_file_name:
        assert not args.input_file_name.endswith(".txt")
        base, _ = os.path.splitext(args.input_file_name)
        args.output_file_name = base + '.txt'
        print(f"Writing output to {args.output_file_name}")
    args.is_nyt = False
    convert_grid(args.input_file_name, **vars(args))


if __name__ == '__main__':
    pass
    # main(["/Users/fy/Desktop/Listener4263.pdf"])

    main(["/Users/fy/Desktop/THEMELESS SATURDAY.pdf", "--puzzle", "--clues", "/Users/fy/Desktop/lines.txt"])
    # main(["/Users/fy/Desktop/foobar.pdf", "--puzzle", ])

    # main(["/Users/fy/Desktop/NYT.png", "--puzzle"])
