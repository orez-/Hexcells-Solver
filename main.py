import re

import PIL.Image

import hex_model
import image_parse
import util

af = '\x1b[38;5;{}m'.format
ab = '\x1b[48;5;{}m'.format
clear = '\x1b[0m'


HEXAGON_RATIO = (3 ** 0.5) / 2  # width * HEXAGON_RATIO = height

hexagon_colors = {
    hex_model.Color.blue: 38,
    hex_model.Color.yellow: 214,
    hex_model.Color.black: 237,
}


def _interpret_text(text):
    """
    Interpret OCR'd text as something we expect.

    All values will be of one of the following forms:
    -\d+-
    \{\d+\}
    \d+
    \?

    Unfortunately, our OCR results are a little fuzzy sometimes, so we
    pass it through this function to make a best guess as to what we're
    looking at.
    """
    patterns = [
        (r'^[-._]+(\d+)[-._]+$', '-{}-'),
        (r'^[\[({]+(\d+)[\])}]+$', '{{{}}}'),
        (r'^(\d+)$', '{}'),
        (r'^(\?)$', '{}'),
    ]
    for pattern, replacement in patterns:
        match = re.match(pattern, text)
        if match:
            return replacement.format(match.group(1))
    raise ValueError("Could not parse {!r}".format(text))


def get_hex_text(im, box):
    """
    Read text from the hex contained in the given box.
    """
    # we chop off the corners of the hex to avoid getting the OCR confused about
    # the shape of the hex vs numbers.
    fourth_width = box.width // 4
    fourth_height = box.height // 4
    hex_img = im.crop((
        box.left + fourth_width, box.top + fourth_height,
        box.right - fourth_width, box.bottom - fourth_height,
    ))
    try:
        return _interpret_text(image_parse.get_text_from_image(hex_img))
    except ValueError as e:
        # If can't determine the value, mechanical turk it for now.
        hex_img.show()
        return input("\n{}: ".format(e))


def is_hexagon(section, box):
    """
    Identify if the given contiguous set of coordinates is a hexagon.
    """
    # TODO: better heuristics for identifying hexagons

    # Ensure the bounding-box is sized like a regular hexagon.
    epsilon = 5
    if abs(box.width * HEXAGON_RATIO - box.height) > epsilon:
        return False

    # Eliminate noise.
    if len(section) < 1000:
        return False

    return True


@util.timeit("Parsin' hexagons")
def parse_hexagons(im, sections):
    origin = None
    board = hex_model.HexBoard()
    for section in sections:
        length = len(section)
        box = image_parse.get_coords_bounding_box(section)
        if not is_hexagon(section, box):
            continue
        center = tuple(sum(coord_set) // length for coord_set in zip(*section))

        if not origin:
            # Arbitrarily call this guy the origin
            spacing = 1.2  # TODO: >:\
            unit = (center[0] - box.left) * spacing
            origin = center
            coord = (0, 0)
        else:
            coord = pixel_to_hex(center[0] - origin[0], center[1] - origin[1], unit)

        # Get pixels that are not white (white is numbers)
        white_pixels, pixels = util.partition_if(
            (im.getpixel((x, y)) for x, y in section),
            lambda value: all(c > 200 for c in value)
        )

        # If speed is an issue here we can probably take many fewer pixels.
        color = tuple(
            sum(component) / length
            for component in zip(*pixels)
        )
        color = hex_model.Color.closest(color)
        text = '-'

        epsilon = 20  # TODO: ᖍ(ツ)ᖌ
        if len(white_pixels) > epsilon:  # enough white pixels to check for a number
            text = get_hex_text(im, box)
        board[coord] = hex_model.Hex(text, color)
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
            # row_num is odd, leftmost is odd, diff one more than you are
            # row_num is even, leftmost is even, diff one more than you are
            last -= 1
        for (x, y, z), hex_ in row:
            color = hexagon_colors[hex_.color]
            print(end='    ' * ((x - last + 1) // 2 - 1))
            print('{}{:^3}{}'.format(af(color), hex_.text, clear), end=' ')  # af or ab are nice here.
            last = x
        print()


def save_debug_board(board):
    try:
        with open('debug_board.txt', 'w') as f:
            f.write(repr(board._board))
    except IOError as e:
        print("Error saving file -", str(e))


def get_debug_board():
    board = hex_model.HexBoard()
    with open('debug_board.txt', 'r') as f:
        board._board = eval(f.read(), vars(hex_model))
    return board


if __name__ == '__main__':
    full = True
    if full:
        im = PIL.Image.open('scrsh.png').convert('RGB')
        selection = image_parse.fuzzy_select(im, 0, 0, threshold=70)
        selection = image_parse.invert_selection(im, selection)
        sections = image_parse.get_contiguous_sections(im, selection)

        board = parse_hexagons(im, sections)
        save_debug_board(board)
    else:
        board = get_debug_board()
    display_board(board)
    solutions = list(board.solve())
    board.apply_clicked()
    print()
    display_board(board)
    print()
