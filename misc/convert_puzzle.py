import argparse
import itertools
import os
import sys
import tempfile
from contextlib import ExitStack
from typing import Optional, List, Any, Set, Tuple, cast, ContextManager, TextIO

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
    num_columns = num_rows = 1
    for num_columns in itertools.count(2):
        square_width = puzzle_w / num_columns
        approximate_column_indices = (contours_x_y_w_h[..., 0] - puzzle_x) / square_width
        column_indices = np.round(approximate_column_indices).astype(int)
        delta = np.max(np.abs(column_indices - approximate_column_indices))
        if delta < .20:
            break

    for num_rows in itertools.count(2):
        square_height = puzzle_h / num_rows
        approximate_row_indices = (contours_x_y_w_h[..., 1] - puzzle_y) / square_height
        row_indices = np.round(approximate_row_indices).astype(int)
        delta = np.max(np.abs(row_indices - approximate_row_indices))
        if delta < .20:
            break

    indices = set()
    for row in range(num_rows):
        for column in range(num_columns):
            x0 = puzzle_x + column * square_width
            y0 = puzzle_y + row * square_height
            x1 = x0 + square_width
            y1 = y0 + square_height
            x0, y0, x1, y1 = round(x0), round(y0), round(x1), round(y1)
            white_count = cv2.countNonZero(thresh2[y0 + 1:y1 - 1, x0 + 1: x1 - 1])
            white_percent = white_count / ((square_width - 2) * (square_height - 2))
            if white_percent >= .75:
                indices.add((row, column))

    # cv2.imwrite("/tmp/foo.jpg", clone)
    # os.system(f"/usr/bin/open /tmp/foo.jpg > /dev/null")
    indices = np.array(sorted(indices))

    # There is some code that I removed that handles the image being rotated. I deleted when I totally re-did
    # this code.
    # https://stackoverflow.com/questions/16975556/crossword-digitization-using-image-processing?rq=1

    handle_nyt_puzzle(num_columns, num_rows, indices, **args)


def handle_nyt_puzzle(no_columns, no_rows, indices,
                      *, copyright: str, title: str, author: str,
                      output_file_name: str,
                      clue_file: str, **_args: Any) -> None:
    # squares = {(row, column) for (column, row) in indices}
    squares = {(row, column) for (row, column) in indices}

    print(f"Grid is {no_rows} rows by {no_columns} columns.")
    print(f"There are {no_rows * no_columns - len(squares)} black squares.")
    asymmetric = [(row, column) for row in range(no_rows) for column in range(no_columns)
                  if ((row, column) in squares) != ((no_rows - row - 1, no_columns - column - 1) in squares)]
    if not asymmetric:
        print(f"The grid is 180º symmetric")
    else:
        for (row, column) in asymmetric:
            print(f'({row} {column}) -> {(row, column) in squares}')
    down_clues = {(row, column) for (row, column) in squares if (row - 1, column) not in squares}
    across_clues = {(row, column) for (row, column) in squares if (row, column - 1) not in squares}
    print(f"There are {len(across_clues)} across clues and {len(down_clues)} down clues.")
    if clue_file:
        clues = _parse_clue_file(clue_file, across_clues, down_clues)
    else:
        clues = ["#"] * (len(across_clues) + len(down_clues))
    with ExitStack() as stack:
        if output_file_name:
            file = stack.enter_context(cast(ContextManager[TextIO], open(output_file_name, "w", encoding="iso-8859-1")))
        else:
            file = sys.stdout
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
        name = file.name

    print(f'open -a "Across Lite" "{name}"')
    os.system(f'open -a "Across Lite" "{name}"')

def _parse_clue_file(clue_file: str, across_clues: Set[Tuple[int, int]], down_clues: Set[Tuple[int, int]]) -> List[str]:
    clue_number_to_location = list(enumerate(sorted(across_clues.union(down_clues)), start=1))
    result = []
    with open(clue_file) as file:
        lines = [stripped for line in file.readlines()
                 for stripped in [line.strip()]
                 if stripped and stripped != 'ACROSS' and stripped != "DOWN"]
        for these_clues, clue_type in ((across_clues, 'A'), (down_clues, 'D')):
            number_and_location = [(i, location) for i, location in clue_number_to_location if location in these_clues]
            for clue_number, location in number_and_location:
                line = lines.pop(0)
                assert line.strip() == str(clue_number), f'For Clue {clue_number} read {line.strip()} from file'
                result.append(lines.pop(0))
    return result


def main(arguments: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description='Process log files.')
    parser.add_argument(action="store", dest="input_file_name", help="file to convert")
    parser.add_argument('--output', '-o', action='store', dest='output_file_name', help="output file name")
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

    main(["/Users/fy/Desktop/THEMELESS SATURDAY.pdf", "--puzzle",
          "--clues", "/Users/fy/Desktop/lines.txt"
          ])

    # main(["/Users/fy/Desktop/NYT.png", "--puzzle"])
