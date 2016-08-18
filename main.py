import re

import PIL.Image

import hex_model
import image_parse
import util

af = '\x1b[38;5;{}m'.format
ab = '\x1b[48;5;{}m'.format
clear = '\x1b[0m'


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


@util.timeit("Parsin' hexagons")
def parse_hexagons(im, sections):
    origin = None
    board = hex_model.HexBoard()
    for section in sections:
        # TODO: better heuristics for identifying hexagons
        length = len(section)
        if not (4000 < length < 5000):
            continue
        center = tuple(sum(coord_set) // length for coord_set in zip(*section))
        left, top, right, bottom = image_parse.get_coords_bounding_box(section)

        if not origin:
            # Arbitrarily call this guy the origin
            spacing = 1.2  # TODO: >:\
            unit = (center[0] - left) * spacing
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
            # we chop off the corners of the hex to avoid getting the OCR confused about
            # the shape of the hex vs numbers.
            fourth_width = (right - left) // 4
            fourth_height = (bottom - top) // 4
            hex_img = im.crop((
                left + fourth_width, top + fourth_height,
                right - fourth_width, bottom - fourth_height,
            ))
            try:
                text = _interpret_text(image_parse.get_text_from_image(hex_img))
            except ValueError as e:
                # If can't determine the value, mechanical turk it for now.
                hex_img.show()
                text = input("\n{}: ".format(e))

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


if __name__ == '__main__':
    full = True
    if full:
        im = PIL.Image.open('scrsh.png').convert('RGB')
        selection = image_parse.fuzzy_select(im, 0, 0, threshold=70)
        selection = image_parse.invert_selection(im, selection)
        sections = image_parse.get_contiguous_sections(im, selection)

        board = parse_hexagons(im, sections)
    else:
        board = hex_model.get_debug_board()
    display_board(board)
    print()
