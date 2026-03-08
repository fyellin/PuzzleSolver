from collections.abc import Sequence

from solver.fill_in_crossword_grid import (
    Entry,
    FillInCrosswordGrid,
    FillInCrosswordGrid4Way,
    FillInCrosswordGridMushed,
    SquareType,
)


def test_numeric_13x13_grid() -> None:
    # fmt: off
    acrosses = (
        (1, '161051'), (5, '2985984'), (10, '406.125'), (12, '3.125'),
        (13, '1105'), (15, '681503'), (16, '56006721'), (19, '24137569'),
        (20, '738639'), (21, '725760'), (23, '2/15'),
        (25, '49.28'), (27, '10/7'), (29, '916839'),
        (31, '170625'), (33, '16777559'), (37, '33534749'), (38, '326592'),
        (39, '1904'), (40, '651.7'), (41, '912.673'), (42, '8168202'), (43, '234256'))

    downs = (
        (1, '1485172'), (2, '161078'), (3, '0.008'), (4, '5156/343'),
        (5, '25/243'),
        (6, '83853'), (7, '5.12'), (8, '9150570'), (9, '45369'), (11, '161172'),
        (14, '1729'),
        # (16.5, "243.153"),
        (17, '266/23'), (18, '23/169'),
        (22, '287/3123'), (24, '1679616'),
        (26, '995328'), (28, '7529536'),
        (30, '153/92'),
        (31, '1955'), (32, '607062'),
        (33, '10368'), (34, '70972'), (35, '149.4'), (36, '85.8'))
    # fmt: on

    filler = FillInCrosswordGrid(acrosses, downs, size=13)
    results = filler.run(debug=5)
    assert len(results) == 1
    for result in results:
        filler.display(result)


def test_numeric_8X10_grid() -> None:
    # fmt: off
    acrosses = [(1, '3541'), (4, '1331'), (8, '2156'), (10, '322'), (12, '324'),
                (14, '45'), (16, '664'), (17, '6416'), (18, '35245'), (19, '51'),
                (21, '64'), (23, '63245'), (25, '2153'), (27, '632'), (29, '54'),
                (30, '314'), (31, '561'), (33, '2512'), (35, '5356'), (36, '3316')]
    downs = [(1, '3136'), (2, '512656'), (3, '42'), (5, '36445'), (6, '3141'),
             (7, '16'), (9, '1314631'), (11, '242'), (13, '2653641'), (15, '5625'),
             (18, '3125'), (20, '143641'), (22, '45325'), (24, '265'), (26, '1463'),
             (28, '2116'), (32, '35'), (34, '23')]
    # fmt: on

    filler = FillInCrosswordGrid(acrosses, downs, width=8, height=10)
    results = filler.run(debug=5)
    # results = filler.no_numbering().run(debug=3)
    assert len(results) == 1
    for result in results:
        filler.display(result)


def test_mushed_grid() -> None:
    # fmt: off
    info = (
         (1, '1737'), (1, '195'), (2, '72'), (3, '731'), (4, '13'), (4, '179'),
         (5, '35'), (6, '92'), (7, '3375'), (8, '512'), (9, '171'), (10, '242'),
         (11, '196'), (12, '608'), (13, '27'), (13, '2744'), (14, '10'), (14, '14'),
         (15, '71'), (16, '2048')
    )
    # fmt: on
    filler = FillInCrosswordGridMushed(info, width=6, height=5)
    # filler = FillInCrosswordGrid(info, width=7, height=7)
    results = filler.run(debug=5)
    assert len(results) == 1
    for result in results:
        filler.display(result)


def test_90_symmetric_grid() -> None:
    # fmt: off
    across_lengths: Sequence[Entry] = [
        6, "abcdefg", 4, 9, 10, 7, 4,
        "qrstuv4", 5, 7, 5, 7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    down_lengths: Sequence[Entry] = [
        7, 9, 7, 7, 5, 4, "e123456789", 4, 6, 7,
        10, 5, 7, 9, 7, 7, 7, 6, 5, 4, 4]
    # fmt: on

    # across_lengths = across_lengths[1:-1]
    # down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4,  7, 10, 5, 7, 9, 7, 7, 7, 5, 4, 4]

    # across_lengths = [6, 7, 4, 9, 10, 7, 4, 7, 5, 7,  7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    #  down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4, 6, 7, 10,  7, 9, 7, 7, 7, 6, 5, 4, 4]

    filler = FillInCrosswordGrid4Way(across_lengths, down_lengths, width=13)
    results = filler.run(debug=100, square_type=SquareType.ANY)
    assert len(results) >= 1
    for result in results:
        filler.display(result)