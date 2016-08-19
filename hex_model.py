import enum
import itertools

import util


class Color(enum.Enum):
    blue = (0x05, 0xa4, 0xeb)
    yellow = (0xff, 0xaf, 0x29)
    black = (0x3e, 0x3e, 0x3e)

    @classmethod
    def closest(self, value):
        """
        Return the enum element closest in color to the given color.

        `value` is a tuple of RGB values.
        """
        return min(Color, key=lambda color: util.color_diff(color.value, value))


def coordinate(x=None, y=None, z=None):
    """
    Standardize and validate a hex coordinate given at least two components.

    A standardized cubic hex coordinate is three axes - x, y, and z -
    where x + y + z = 0. Given two components, this function will
    calculate the third and return all three. Given three components,
    this function will validate that the invariant above is met and
    will raise a ValueError if it is not, otherwise returning all three.
    """
    coords = x, y, z
    nones = sum(c is None for c in coords)
    if nones > 1:
        raise TypeError("At least two coordinate values must be provided.")
    if nones == 1:
        final_coord = -sum(c for c in coords if c is not None)
        coords = tuple(c if c is not None else final_coord for c in coords)
    elif sum(coords):
        raise ValueError("Coordinate values must sum to 0.")
    return coords


def coordinate_by_key(key):
    """
    Given a key, return a standardized coordinate.

    A key may be an iterable representing x, y, and optionally z.
    A key may also be a dictionary with at least two of x, y, and z.
    """
    return coordinate(**key) if isinstance(key, dict) else coordinate(*key)


def parse_clue(text):
    """
    Parse the text of a clue.

    Returns (integer value, contiguous)
    If the clue indicates the values must be contiguous, `contiguous` is True.
    If the clue indicates the values must NOT be contiguous, `contiguous` is False.
    If the clue does not indicate whether the values must be contiguous or not,
        `contiguous` is None.
    """
    if text == '-':
        return None, None
    if text.startswith('-'):
        return int(text[1:-1]), False
    if text.startswith('{'):
        return int(text[1:-1]), True
    try:
        return int(text), None
    except ValueError:
        return None, None


class Hex:
    def __init__(self, text, color):
        self.value, self.contiguous = parse_clue(text)
        self.color = color

    @property
    def text(self):
        if self.value is None:
            return '-'
        fmt = {
            None: '{}',
            True: '{{{}}}',
            False: '-{}-',
        }[self.contiguous]
        return fmt.format(self.value)

    def __repr__(self):
        return '{}({!r}, Color.{})'.format(type(self).__name__, self.text, self.color.name)


class HexBoard:
    def __init__(self):
        self._board = {}

    def __setitem__(self, key, value):
        coord = coordinate_by_key(key)
        self._board[coord] = value

    @property
    def rows(self):
        """
        Yield left-to-right rows of hexes from top-to-bottom, for display.

        A "row" represents a set of hexagons whose centers are at the
        same vertical position. For flat-topped hexagons, this means
        (perhaps unintuitively) that sequential entries in a row will be
        two x coordinates apart from one another and will share no edge
        or vertex.

        Each yield is composed of a "row number" and the row itself. The
        row number represents the row's vertical positioning relative to
        the other rows: sequential rows will have sequential row
        numbers. Each row is composed of its hex coordinate and the Hex
        object at that coordinate.
        """
        def sort_key(x_y_z__value):
            (x, y, z), value = x_y_z__value
            return y - z, x

        def group_key(x_y_z__value):
            (x, y, z), value = x_y_z__value
            return y - z

        data = sorted(self._board.items(), key=sort_key)
        return itertools.groupby(data, group_key)

    @property
    def leftmost(self):
        """
        The x value of the leftmost hex in the board.
        """
        if not self._board:
            raise ValueError("empty board")
        return min(x for x, y, z in self._board)


def get_debug_board():
    # TODO - delete or move me.
    board = HexBoard()
    board._board = {
        (-4, 6, -2): Hex('-', Color.yellow),
        (-7, 2, 5): Hex('-', Color.yellow),
        (12, 2, -14): Hex('-', Color.yellow),
        (7, -4, -3): Hex('-', Color.yellow),
        (11, -4, -7): Hex('-', Color.yellow),
        (4, -2, -2): Hex('4', Color.black),
        (-3, -2, 5): Hex('-', Color.yellow),
        (-2, 8, -6): Hex('-', Color.yellow),
        (12, -7, -5): Hex('-', Color.yellow),
        (-7, 3, 4): Hex('-', Color.yellow),
        (7, 2, -9): Hex('-', Color.yellow),
        (12, -2, -10): Hex('-', Color.yellow),
        (9, 2, -11): Hex('-', Color.yellow),
        (6, 6, -12): Hex('-', Color.yellow),
        (4, 2, -6): Hex('-', Color.yellow),
        (11, -8, -3): Hex('-', Color.yellow),
        (11, 3, -14): Hex('-', Color.yellow),
        (-5, -1, 6): Hex('-', Color.yellow),
        (-7, 5, 2): Hex('-', Color.yellow),
        (13, -4, -9): Hex('-', Color.yellow),
        (6, 1, -7): Hex('-', Color.blue),
        (12, -5, -7): Hex('-', Color.yellow),
        (0, -4, 4): Hex('-', Color.yellow),
        (-3, 5, -2): Hex('-', Color.yellow),
        (5, 6, -11): Hex('3', Color.black),
        (4, -5, 1): Hex('-', Color.yellow),
        (5, -1, -4): Hex('-', Color.yellow),
        (3, 3, -6): Hex('-', Color.yellow),
        (0, 6, -6): Hex('-', Color.yellow),
        (-5, 9, -4): Hex('-', Color.yellow),
        (11, -5, -6): Hex('2', Color.black),
        (3, -3, 0): Hex('-', Color.yellow),
        (0, 9, -9): Hex('-', Color.yellow),
        (6, 3, -9): Hex('-', Color.yellow),
        (9, 3, -12): Hex('-', Color.yellow),
        (-3, 3, 0): Hex('{3}', Color.black),
        (10, -6, -4): Hex('-', Color.yellow),
        (9, 4, -13): Hex('-', Color.yellow),
        (-6, 0, 6): Hex('-', Color.yellow),
        (-2, 1, 1): Hex('-', Color.yellow),
        (5, 1, -6): Hex('-', Color.yellow),
        (1, -1, 0): Hex('-', Color.yellow),
        (3, -4, 1): Hex('-', Color.yellow),
        (4, 5, -9): Hex('-', Color.yellow),
        (1, 8, -9): Hex('-', Color.yellow),
        (-4, 4, 0): Hex('-', Color.yellow),
        (8, -6, -2): Hex('-', Color.yellow),
        (13, -5, -8): Hex('-', Color.yellow),
        (-5, 2, 3): Hex('-', Color.yellow),
        (-5, 5, 0): Hex('-', Color.yellow),
        (6, -3, -3): Hex('{4}', Color.black),
        (11, 2, -13): Hex('-', Color.yellow),
        (2, 3, -5): Hex('-', Color.yellow),
        (-7, 6, 1): Hex('-', Color.yellow),
        (-4, 0, 4): Hex('-', Color.yellow),
        (-5, 8, -3): Hex('-', Color.yellow),
        (8, -1, -7): Hex('-', Color.yellow),
        (9, 1, -10): Hex('-', Color.yellow),
        (8, -8, 0): Hex('-', Color.yellow),
        (-4, -1, 5): Hex('-', Color.yellow),
        (10, 1, -11): Hex('-', Color.yellow),
        (2, -1, -1): Hex('-', Color.yellow),
        (4, -3, -1): Hex('-', Color.yellow),
        (13, 0, -13): Hex('-', Color.yellow),
        (3, 2, -5): Hex('3', Color.black),
        (-4, 11, -7): Hex('-', Color.yellow),
        (4, -6, 2): Hex('-', Color.yellow),
        (13, -1, -12): Hex('-', Color.yellow),
        (-7, 7, 0): Hex('-', Color.yellow),
        (-6, 2, 4): Hex('-', Color.yellow),
        (1, -4, 3): Hex('-', Color.yellow),
        (-7, 9, -2): Hex('-', Color.yellow),
        (8, -4, -4): Hex('3', Color.black),
        (6, -4, -2): Hex('-', Color.yellow),
        (8, -7, -1): Hex('-', Color.yellow),
        (-3, 2, 1): Hex('-', Color.yellow),
        (1, -2, 1): Hex('-', Color.yellow),
        (-4, 3, 1): Hex('-', Color.yellow),
        (0, 7, -7): Hex('-', Color.yellow),
        (4, -4, 0): Hex('-', Color.yellow),
        (2, 0, -2): Hex('-', Color.blue),
        (-3, 0, 3): Hex('-', Color.yellow),
        (4, 4, -8): Hex('-', Color.yellow),
        (0, -1, 1): Hex('-', Color.yellow),
        (-6, 11, -5): Hex('-', Color.yellow),
        (7, 1, -8): Hex('5', Color.blue),
        (-2, -1, 3): Hex('-', Color.yellow),
        (7, 3, -10): Hex('-', Color.yellow),
        (12, -9, -3): Hex('-', Color.yellow),
        (-5, 11, -6): Hex('-', Color.yellow),
        (5, 0, -5): Hex('-', Color.yellow),
        (-1, 8, -7): Hex('-', Color.yellow),
        (6, -2, -4): Hex('-', Color.yellow),
        (9, 0, -9): Hex('-', Color.yellow),
        (10, -5, -5): Hex('-', Color.yellow),
        (-6, 8, -2): Hex('1', Color.black),
        (-5, 7, -2): Hex('-', Color.yellow),
        (0, -2, 2): Hex('-', Color.yellow),
        (1, 0, -1): Hex('-', Color.yellow),
        (4, -1, -3): Hex('-', Color.yellow),
        (3, -1, -2): Hex('-', Color.yellow),
        (0, 0, 0): Hex('-', Color.yellow),
        (9, -2, -7): Hex('6', Color.blue),
        (-6, 5, 1): Hex('-', Color.yellow),
        (0, 3, -3): Hex('-', Color.yellow),
        (-3, 9, -6): Hex('-', Color.yellow),
        (-7, 10, -3): Hex('-', Color.yellow),
        (-2, 7, -5): Hex('-', Color.yellow),
        (10, -8, -2): Hex('3', Color.blue),
        (-4, 1, 3): Hex('-', Color.yellow),
        (10, 2, -12): Hex('-', Color.yellow),
        (-3, -1, 4): Hex('4', Color.black),
        (-2, 5, -3): Hex('-', Color.yellow),
        (11, -1, -10): Hex('-', Color.yellow),
        (8, -5, -3): Hex('-', Color.yellow),
        (8, 1, -9): Hex('-', Color.yellow),
        (-3, 1, 2): Hex('-', Color.yellow),
        (10, -2, -8): Hex('-', Color.yellow),
        (1, 1, -2): Hex('-', Color.yellow),
        (2, 1, -3): Hex('-', Color.yellow),
        (7, -6, -1): Hex('-', Color.yellow),
        (1, 3, -4): Hex('-', Color.yellow),
        (2, 7, -9): Hex('-', Color.yellow),
        (5, -6, 1): Hex('-', Color.yellow),
        (11, -3, -8): Hex('-3-', Color.black),
        (0, -3, 3): Hex('-', Color.yellow),
        (7, 0, -7): Hex('-', Color.yellow),
        (-6, 9, -3): Hex('-', Color.yellow),
        (12, 0, -12): Hex('-', Color.yellow),
        (-3, 10, -7): Hex('-', Color.yellow),
        (0, 2, -2): Hex('-', Color.yellow),
        (5, -2, -3): Hex('-', Color.yellow),
        (7, 5, -12): Hex('-', Color.yellow),
        (-1, 3, -2): Hex('-', Color.yellow),
        (-2, 9, -7): Hex('-', Color.yellow),
        (5, -5, 0): Hex('-', Color.yellow),
        (-1, 1, 0): Hex('3', Color.black),
        (7, -7, 0): Hex('-', Color.yellow),
        (9, -3, -6): Hex('-', Color.blue),
        (-1, 7, -6): Hex('-', Color.yellow),
        (10, -7, -3): Hex('-', Color.blue),
        (4, 0, -4): Hex('3', Color.black),
        (-5, 4, 1): Hex('-', Color.yellow),
        (8, 5, -13): Hex('-', Color.yellow),
        (10, -9, -1): Hex('-', Color.yellow),
        (13, -2, -11): Hex('-', Color.yellow),
        (-6, 1, 5): Hex('-', Color.yellow),
        (9, -5, -4): Hex('-', Color.yellow),
        (0, 1, -1): Hex('-', Color.yellow),
        (3, 4, -7): Hex('-', Color.yellow),
        (0, 5, -5): Hex('-', Color.yellow),
        (-4, -2, 6): Hex('-', Color.yellow),
        (6, 4, -10): Hex('-', Color.yellow),
        (-6, 10, -4): Hex('-', Color.yellow),
        (3, 7, -10): Hex('-', Color.yellow),
        (1, 6, -7): Hex('-', Color.yellow),
        (-1, 4, -3): Hex('4', Color.black),
        (13, -7, -6): Hex('-', Color.yellow),
        (0, 4, -4): Hex('-', Color.yellow),
        (2, 5, -7): Hex('-', Color.yellow),
        (7, -1, -6): Hex('3', Color.black),
        (12, 1, -13): Hex('-', Color.yellow),
        (8, -2, -6): Hex('-', Color.yellow),
        (7, 4, -11): Hex('-', Color.yellow),
        (10, -1, -9): Hex('-', Color.yellow),
        (-4, 7, -3): Hex('-', Color.yellow),
        (-2, 2, 0): Hex('-', Color.yellow),
        (5, 3, -8): Hex('-', Color.yellow),
        (1, 4, -5): Hex('-', Color.yellow),
        (-2, 6, -4): Hex('-', Color.yellow),
        (2, 2, -4): Hex('2', Color.black),
        (12, -3, -9): Hex('-', Color.yellow),
        (7, -3, -4): Hex('-', Color.yellow),
        (2, 8, -10): Hex('-', Color.yellow),
        (-1, -3, 4): Hex('-', Color.yellow),
        (6, -7, 1): Hex('1', Color.black),
        (4, 1, -5): Hex('-', Color.yellow),
        (3, -5, 2): Hex('-', Color.yellow),
        (1, 5, -6): Hex('-', Color.yellow),
        (-3, 6, -3): Hex('-', Color.yellow),
        (6, 0, -6): Hex('2', Color.black),
        (12, -6, -6): Hex('-', Color.yellow),
        (11, 0, -11): Hex('-', Color.yellow),
        (2, -4, 2): Hex('-', Color.yellow),
        (7, -5, -2): Hex('-', Color.yellow),
        (-1, -1, 2): Hex('-', Color.yellow),
        (-4, 8, -4): Hex('-', Color.yellow),
        (-2, 3, -1): Hex('-', Color.yellow),
        (10, -3, -7): Hex('-4-', Color.black),
        (3, 6, -9): Hex('-', Color.yellow),
        (13, -8, -5): Hex('-', Color.yellow),
        (6, 5, -11): Hex('-', Color.yellow),
        (-6, 3, 3): Hex('-', Color.yellow),
        (11, -7, -4): Hex('-', Color.yellow),
        (5, 5, -10): Hex('-', Color.yellow),
        (-6, 6, 0): Hex('-', Color.yellow),
        (-4, 10, -6): Hex('-', Color.yellow),
        (5, 2, -7): Hex('-', Color.yellow),
        (11, -9, -2): Hex('-', Color.yellow),
    }
    return board
