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

