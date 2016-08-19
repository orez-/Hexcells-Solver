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


def generate_hex_circle(distance):
    return (
       (x, y, -x - y)
       for x in range(-distance, distance + 1)
       for y in range(max(-distance, -distance - x), min(distance, distance - x) + 1)
    )


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
        self._regions = None

    def __getitem__(self, key):
        coord = coordinate_by_key(key)
        return self._board[coord]

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

    def _neighbors(self, coord, distance=1):
        return {
            neighbor for neighbor in (
                tuple(map(sum, zip(coord, delta)))
                for delta in generate_hex_circle(distance)
                if any(delta)  # don't yield yourself
            ) if neighbor in self._board
        }

    def _get_simplified_region(self, hexes, value, projected=()):
        filtered_hexes = set()
        for coord in hexes:
            if coord in projected:
                color = projected[coord]
            else:
                color = self._board[coord].color
            if color == Color.yellow:
                filtered_hexes.add(coord)
            elif color == Color.blue:
                value -= 1
            # do nothing with black.
        assert value >= 0, value
        assert value <= len(filtered_hexes), (value, len(filtered_hexes))
        return frozenset(filtered_hexes), value

    def _populate_regions(self):
        """
        Process information into generic regions with values.
        """
        self._regions = {}
        for coord, hex_ in self._board.items():
            if hex_.value is None:
                continue
            distance = 1 if hex_.color == Color.black else 2
            hexes, value = self._get_simplified_region(self._neighbors(coord, distance), hex_.value)
            self._regions[hexes] = value

    def _identify_solved_regions(self, projected):
        projected = {} if projected is True else dict(projected)
        solutions = set()
        new_regions = {}
        for hexes, value in self._regions.items():
            hexes, value = self._get_simplified_region(hexes, value, projected)
            if len(hexes) == value:
                solutions.update((hex_, Color.blue) for hex_ in hexes)
            elif value == 0:
                solutions.update((hex_, Color.black) for hex_ in hexes)
            else:
                new_regions[hexes] = value
        return solutions, new_regions

    def _subdivide_overlapping_regions(self):
        # examine overlapping regions
        new_regions = {}
        # compare each region to each other
        for (hexes1, value1), (hexes2, value2) in itertools.combinations(self._regions.items(), 2):
            overlap = frozenset(hexes1 & hexes2)
            if not overlap:
                continue

            hexes1_exclusive = frozenset(hexes1 - overlap)
            hexes2_exclusive = frozenset(hexes2 - overlap)
            # find the upper and lower bounds for each that can fit in the overlap.
            omax = min(len(overlap), value2, value1)
            omin = max(
                value2 - len(hexes2_exclusive),
                value1 - len(hexes1_exclusive),
                0,
            )
            if omin == omax:
                if overlap not in self._regions:
                    new_regions[overlap] = omax
                if hexes1_exclusive not in self._regions:
                    new_regions[hexes1_exclusive] = value1 - omax
                if hexes2_exclusive not in self._regions:
                    new_regions[hexes2_exclusive] = value2 - omax
        return new_regions

    def solve(self):
        """
        Yield new information that can be inferred from the board state.
        """
        self._populate_regions()

        progress = True
        while progress:
            # Identify newly-solved regions
            solutions = True
            while solutions:
                solutions, self._regions = self._identify_solved_regions(solutions)
                yield from solutions

            new_regions = self._subdivide_overlapping_regions()
            progress = bool(new_regions)
            self._regions.update(new_regions)
