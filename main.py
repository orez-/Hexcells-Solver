import collections
import functools
import itertools
import sys
import time

from PIL import Image


def timeit(msg):
    def decorator(fn):
        @functools.wraps(fn)
        def anon(*args, **kwargs):
            print(msg, end='')
            sys.stdout.flush()
            t = time.time()
            result = fn(*args, **kwargs)
            print(' - {:.1f}s'.format(time.time() - t))
            return result
        return anon
    return decorator


def bfs(im, x, y, predicate):
    width, height = im.size
    result = {(x, y)}
    seen = {(x, y)}
    q = collections.deque(result)
    while q:
        tx, ty = q.popleft()
        for nx, ny in [(tx, ty - 1), (tx, ty + 1), (tx - 1, ty), (tx + 1, ty)]:
            # if not in bounds, or already seen
            if not (0 <= nx < width and 0 <= ny < height) or (nx, ny) in seen:
                continue
            seen.add((nx, ny))
            if predicate(nx, ny):
                result.add((nx, ny))
                q.append((nx, ny))
    return result


@timeit("Beginning fuzzy select")
def fuzzy_select(im, x, y, threshold=15):
    threshold *= 3  # ᖍ(ツ)ᖌ
    rgb = im.getpixel((x, y))

    def predicate(x, y):
        neighbor_rgb = im.getpixel((x, y))
        return sum(abs(a - b) for a, b in zip(rgb, neighbor_rgb)) <= threshold

    return bfs(im, x, y, predicate)


@timeit("Inverting selection")
def invert_selection(im, selection):
    width, height = im.size
    return set((x, y) for x in range(width) for y in range(height) if (x, y) not in selection)


@timeit("Getting contiguous sections")
def get_contiguous_sections(im, selection):
    selection = set(selection)

    def predicate(x, y):
        return (x, y) in selection

    while selection:
        x, y = selection.pop()
        result = bfs(im, x, y, predicate)
        yield result
        selection -= result


def coordinate_by_key(key):
    return coordinate(**key) if isinstance(key, dict) else coordinate(*key)


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


@timeit("Parsin' hexagons")
def parse_hexagons(sections):
    origin = None
    board = HexBoard()
    for section in sections:
        # TODO: better heuristics for identifying hexagons
        if 4000 < len(section) < 5000:
            center = tuple(sum(coord_set) // len(section) for coord_set in zip(*section))
            if not origin:
                leftmost = min(next(zip(*section)))
                spacing = 1.2  # TODO: >:\
                unit = (center[0] - leftmost) * spacing
                origin = center
                coord = (0, 0)
            else:
                coord = pixel_to_hex(center[0] - origin[0], center[1] - origin[1], unit)
            board[coord] = 1
    return board


def pixel_to_hex(x, y, size):
    q = x * 2/3 / size
    r = (-x / 3 + (3 ** 0.5)/3 * y) / size
    return round(q), round(r)


def display_board(board):
    """
    Display the board of flat-top hexes.
    """
    leftmost = board.leftmost
    for row_num, row in board.rows:
        bump = (row_num % 2) != (leftmost % 2)
        last = leftmost
        if bump:
            # leftmost is even, align even x's on left
            # leftmost is odd, align odd x's on left
            print(end='  ')
        else:
            # row_id is odd, leftmost is odd, diff one more than you are
            # row_id is even, leftmost is even, diff one more than you are
            last -= 1
        for (x, y, z), value in row:
            print(end='    ' * ((x - last + 1) // 2 - 1))
            print(value, end='   ')
            last = x
        print()


if __name__ == '__main__':
    im = Image.open('scrsh.png')
    selection = fuzzy_select(im, 0, 0, threshold=70)
    selection = invert_selection(im, selection)
    sections = get_contiguous_sections(im, selection)

    board = parse_hexagons(sections)

    # board = HexBoard()
    # board._board = {(-4, 6, -2): 1, (-7, 2, 5): 1, (12, 2, -14): 1, (7, -4, -3): 1, (11, -4, -7): 1, (4, -2, -2): 1, (-3, -2, 5): 1, (-2, 8, -6): 1, (12, -7, -5): 1, (-7, 3, 4): 1, (7, 2, -9): 1, (12, -2, -10): 1, (9, 2, -11): 1, (6, 6, -12): 1, (4, 2, -6): 1, (11, -8, -3): 1, (11, 3, -14): 1, (-5, -1, 6): 1, (-7, 5, 2): 1, (13, -4, -9): 1, (6, 1, -7): 1, (12, -5, -7): 1, (0, -4, 4): 1, (-3, 5, -2): 1, (5, 6, -11): 1, (4, -5, 1): 1, (5, -1, -4): 1, (3, 3, -6): 1, (0, 6, -6): 1, (-5, 9, -4): 1, (11, -5, -6): 1, (3, -3, 0): 1, (0, 9, -9): 1, (6, 3, -9): 1, (9, 3, -12): 1, (-3, 3, 0): 1, (10, -6, -4): 1, (9, 4, -13): 1, (-6, 0, 6): 1, (-2, 1, 1): 1, (5, 1, -6): 1, (1, -1, 0): 1, (3, -4, 1): 1, (4, 5, -9): 1, (1, 8, -9): 1, (-4, 4, 0): 1, (8, -6, -2): 1, (13, -5, -8): 1, (-5, 2, 3): 1, (-5, 5, 0): 1, (6, -3, -3): 1, (11, 2, -13): 1, (2, 3, -5): 1, (-7, 6, 1): 1, (-4, 0, 4): 1, (-5, 8, -3): 1, (8, -1, -7): 1, (9, 1, -10): 1, (8, -8, 0): 1, (-4, -1, 5): 1, (10, 1, -11): 1, (2, -1, -1): 1, (4, -3, -1): 1, (13, 0, -13): 1, (3, 2, -5): 1, (-4, 11, -7): 1, (4, -6, 2): 1, (13, -1, -12): 1, (-7, 7, 0): 1, (-6, 2, 4): 1, (1, -4, 3): 1, (-7, 9, -2): 1, (8, -4, -4): 1, (6, -4, -2): 1, (8, -7, -1): 1, (-3, 2, 1): 1, (1, -2, 1): 1, (-4, 3, 1): 1, (0, 7, -7): 1, (4, -4, 0): 1, (2, 0, -2): 1, (-3, 0, 3): 1, (4, 4, -8): 1, (0, -1, 1): 1, (-6, 11, -5): 1, (7, 1, -8): 1, (-2, -1, 3): 1, (7, 3, -10): 1, (12, -9, -3): 1, (-5, 11, -6): 1, (5, 0, -5): 1, (-1, 8, -7): 1, (6, -2, -4): 1, (9, 0, -9): 1, (10, -5, -5): 1, (-6, 8, -2): 1, (-5, 7, -2): 1, (0, -2, 2): 1, (1, 0, -1): 1, (4, -1, -3): 1, (3, -1, -2): 1, (0, 0, 0): 1, (9, -2, -7): 1, (-6, 5, 1): 1, (0, 3, -3): 1, (-3, 9, -6): 1, (-7, 10, -3): 1, (-2, 7, -5): 1, (10, -8, -2): 1, (-4, 1, 3): 1, (10, 2, -12): 1, (-3, -1, 4): 1, (-2, 5, -3): 1, (11, -1, -10): 1, (8, -5, -3): 1, (8, 1, -9): 1, (-3, 1, 2): 1, (10, -2, -8): 1, (1, 1, -2): 1, (2, 1, -3): 1, (7, -6, -1): 1, (1, 3, -4): 1, (2, 7, -9): 1, (5, -6, 1): 1, (11, -3, -8): 1, (0, -3, 3): 1, (7, 0, -7): 1, (-6, 9, -3): 1, (12, 0, -12): 1, (-3, 10, -7): 1, (0, 2, -2): 1, (5, -2, -3): 1, (7, 5, -12): 1, (-1, 3, -2): 1, (-2, 9, -7): 1, (5, -5, 0): 1, (-1, 1, 0): 1, (7, -7, 0): 1, (9, -3, -6): 1, (-1, 7, -6): 1, (10, -7, -3): 1, (4, 0, -4): 1, (-5, 4, 1): 1, (8, 5, -13): 1, (10, -9, -1): 1, (13, -2, -11): 1, (-6, 1, 5): 1, (9, -5, -4): 1, (0, 1, -1): 1, (3, 4, -7): 1, (0, 5, -5): 1, (-4, -2, 6): 1, (6, 4, -10): 1, (-6, 10, -4): 1, (3, 7, -10): 1, (1, 6, -7): 1, (-1, 4, -3): 1, (13, -7, -6): 1, (0, 4, -4): 1, (2, 5, -7): 1, (7, -1, -6): 1, (12, 1, -13): 1, (8, -2, -6): 1, (7, 4, -11): 1, (10, -1, -9): 1, (-4, 7, -3): 1, (-2, 2, 0): 1, (5, 3, -8): 1, (1, 4, -5): 1, (-2, 6, -4): 1, (2, 2, -4): 1, (12, -3, -9): 1, (7, -3, -4): 1, (2, 8, -10): 1, (-1, -3, 4): 1, (6, -7, 1): 1, (4, 1, -5): 1, (3, -5, 2): 1, (1, 5, -6): 1, (-3, 6, -3): 1, (6, 0, -6): 1, (12, -6, -6): 1, (11, 0, -11): 1, (2, -4, 2): 1, (7, -5, -2): 1, (-1, -1, 2): 1, (-4, 8, -4): 1, (-2, 3, -1): 1, (10, -3, -7): 1, (3, 6, -9): 1, (13, -8, -5): 1, (6, 5, -11): 1, (-6, 3, 3): 1, (11, -7, -4): 1, (5, 5, -10): 1, (-6, 6, 0): 1, (-4, 10, -6): 1, (5, 2, -7): 1, (11, -9, -2): 1}
    display_board(board)
    print()
