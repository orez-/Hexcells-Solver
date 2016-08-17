import itertools


def coordinate(x=None, y=None, z=None):
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
    return coordinate(**key) if isinstance(key, dict) else coordinate(*key)


class HexBoard:
    def __init__(self):
        self._board = {}

    def __setitem__(self, key, value):
        coord = coordinate_by_key(key)
        self._board[coord] = value

    @property
    def rows(self):
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
        return min(x for x, y, z in self._board)
