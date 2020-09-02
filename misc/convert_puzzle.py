import argparse
import os
from typing import Optional, List

import cv2
import numpy as np


def convert_grid(input_name: str, output_name: str, *, title: str, author: str, copyright: str, **_args) -> None:
    img = cv2.imread(input_name)

    # convert the puzzle into a format that findContours can use.  This is magic to me.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    thresh2 = cv2.bitwise_not(thresh)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, 1)

    # Look at the contours whose approximating polygon is a 4-sided polygon (hopefully, a rectangle), and take the one
    # that has the largest area.  This should be the entire puzzle grid.
    # This is the contour representing the entire puzzle
    _, puzzle_contour_index = max((cv2.contourArea(contour), index) for index, contour in enumerate(contours)
                                  for approx in [cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)]
                                  if len(approx) == 4)

    puzzle_x, puzzle_y, puzzle_width, puzzle_height = cv2.boundingRect(contours[puzzle_contour_index])

    # The contours that are immediate descendants of the puzzle_contour index are the white squares.
    bounding_rectangles = []
    for contour, (_next, _prev, _child, parent) in zip(contours, hierarchy[0]):
        if parent == puzzle_contour_index:
            x, y, w, h = rectangle = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            not_black_count = cv2.countNonZero(thresh2[y:y + h, x:x + w])
            assert not_black_count >= .75 * area  # double check the square really is what we think it is
            bounding_rectangles.append(rectangle)

    # Collect up the <x, y> components and the <width, height> components into numpy arrays
    contours_x_y_w_h = np.array(bounding_rectangles)
    contours_x_y = contours_x_y_w_h[..., :2]
    contours_w_h = contours_x_y_w_h[..., 2:]

    # We figure out the average width and height, divide those into the actual width and height, and round to determine
    # the number of rows and columns.  We then work backwards to figure out what the actual width and height of each
    # square should be.
    average_width_height = np.average(contours_w_h, axis=0)
    number_columns_and_rows = np.round([puzzle_width, puzzle_height] / average_width_height)
    no_columns, no_rows = number_columns_and_rows.astype(int)
    square_width_height = [puzzle_width, puzzle_height] / number_columns_and_rows

    # For each <x, y> pair, we convert it into an index by subtracting off the location of the top left point, and
    # dividing by the width and height of a box, and rounding.
    approximate_indices = (contours_x_y - [puzzle_x, puzzle_y]) / square_width_height
    indices = np.round(approximate_indices).astype(int)
    # We hope deltas is small, because it gives us an indication of how far off we are from the truth.
    max_delta = np.max(np.abs(indices - approximate_indices))
    # Convert the indices into a set, but make it row-first rather than x-first.
    squares = {(row, column) for column, row in indices}

    # There is some code that I removed that handles the image being rotated. I deleted when I totally re-did
    # this code.
    # https://stackoverflow.com/questions/16975556/crossword-digitization-using-image-processing?rq=1

    # Print some information for the caller, so they have a reasonable way of checking we got the right ansswer.
    print(f"Grid is {no_rows} rows by {no_columns} columns.")
    print(f"There are {no_rows * no_columns - len(squares)} black squares.")
    is_symmetric = all(((row, column) in squares) == ((no_rows - row - 1, no_columns - column - 1) in squares)
                       for row in range(no_rows) for column in range(no_columns))
    print(f"The grid is {'' if is_symmetric else 'not '}180º symmetric")
    print(f"Max wrongness of approximation is {max_delta:6.3}.  (Below .1 is good)")

    down_clues = {(row, column) for (row, column) in squares if (row - 1, column) not in squares}
    across_clues = {(row, column) for (row, column) in squares if (row, column - 1) not in squares}
    print(f"There are {len(across_clues)} across clues and {len(down_clues)} down clues.")

    with open(output_name, "w") as file:
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
        file.write("#\n" * len(across_clues))
        file.write("<DOWN>\n")
        file.write("#\n" * len(down_clues))
        file.write("<NOTEPAD>\n")


def main(arguments: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description='Process log files.')
    parser.add_argument(action="store", dest="input_file_name", help="file to convert")
    parser.add_argument('--output', '-o', action='store', dest='output_file_name', help="outupt file name")
    parser.add_argument('--title', action='store', dest='title', help="title of puzzle", default="")
    parser.add_argument('--author', action='store', dest='author', help="author of puzzle", default="")
    parser.add_argument('--copyright', action='store', dest='copyright', help="copyright notice", default="")
    args = parser.parse_args(arguments)
    if not args.output_file_name:
        assert not args.input_file_name.endswith(".txt")
        base, _ = os.path.splitext(args.input_file_name)
        args.output_file_name = base + '.txt'
        print(f"Writing output to {args.output_file_name}")
    convert_grid(args.input_file_name, args.output_file_name, **vars(args))


if __name__ == '__main__':
    main(['/users/fy/Desktop/Aug2920.png',
          '--author', "Michael Hawkins",
          '--title', "The New York Times",
          '--copyright', '2020'])
