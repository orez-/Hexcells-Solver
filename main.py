import argparse
import re
import time

import numpy
import pyautogui
import PIL.Image

import hex_model
import image_parse
import screen
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
    hex_img = im.crop(box)
    try:
        return _interpret_text(image_parse.get_text_from_image(hex_img))
    except ValueError as e:
        # If can't determine the value, mechanical turk it for now.
        hex_img.show()
        return input("\n{}: ".format(e))


def is_hexagon(box):
    """
    Identify if the given contiguous set of coordinates is a hexagon.
    """
    # TODO: better heuristics for identifying hexagons

    # Ensure the bounding-box is sized like a regular hexagon.
    epsilon = 5
    if abs(box.width * HEXAGON_RATIO - box.height) > epsilon:
        return False

    # Eliminate noise.
    if box.width * box.height < 5000:
        return False

    return True


@util.timeit("Parsin' labeled hexagons")
def parse_labeled_hexagons(im, im_data, label_array, objs):
    origin = None
    board = hex_model.HexBoard()
    for box in objs:
        if not is_hexagon(box):
            continue
        center = box.center

        if not origin:
            # Arbitrarily call this guy the origin
            spacing = 1.135  # TODO: >:\
            unit = (center[0] - box.left) * spacing
            origin = center
            coord = (0, 0)
        else:
            coord = pixel_to_hex(center[0] - origin[0], center[1] - origin[1], unit)

        assert coord not in board, coord
        board[coord] = read_hex(im, im_data, label_array, box)
    return board


def read_hex(im, im_data, label_array, box):
    # Average the colors of all the pixels in the hex.
    # TODO - figure out how to apply a mask
    #        to only check pixels IN the hex.
    flattened_img = im_data[box.slice].reshape(-1, im_data.shape[-1])
    avg_color = tuple(numpy.mean(flattened_img, axis=0))
    color = hex_model.Color.closest(avg_color)
    text = '-'

    # Check for if there is text on the hex.
    if not label_array[box.text_box.slice].all():
        text = get_hex_text(im, box.text_box)

    return hex_model.Hex(
        text=text,
        color=color,
        image_section=box,
    )


def pixel_to_hex(x, y, size):
    q = x * 2/3 / size
    r = (-x / 3 + (3 ** 0.5)/3 * y) / size
    if round(q * 2) % 2 or round(r * 2) % 2:
        print("Warning - hex estimation dangerously inaccurate: ", (q, r), (x, y))
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
            color = af(color)
            if x == y == z == 0:
                color += ab(237)
            print(end='    ' * ((x - last + 1) // 2 - 1))
            print('{}{:^3}{}'.format(color, hex_.text, clear), end=' ')
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


def read_board(im):
    im = im.convert('RGB')
    im_data, label_array, objs = image_parse.label(im)
    board = parse_labeled_hexagons(im, im_data, label_array, objs)
    save_debug_board(board)
    return board


def apply_commands(board, commands, topleft):
    """
    Run commands against the running game app.
    """
    buttons = {
        hex_model.Color.blue: 'left',
        hex_model.Color.black: 'right',
    }

    dx, dy = topleft
    for coord, color in commands:
        x, y = board[coord].image_section.center
        # TODO - dpi???
        pyautogui.click(x // 2 + dx, y // 2 + dy, button=buttons[color])

    # If we just solved the board, the "game solved" overlay has showed up,
    # and we should not attempt to parse the board again.
    # TODO: that having been said, we might want to look for the overlay
    #       to verify that we didn't mess up?
    if board.is_solved:
        return

    # Hexcells has a fun yellow confetti explosion when you click a cell.
    # Unfortunately this fun confetti makes it into our screenshot, and
    # tesseract loses its mind trying to read it. We wait for the confetti
    # to clear before taking a screenshot.
    time.sleep(2)
    im, _ = screen.grab_game_screen()
    im = im.convert('RGB')
    # TODO: we know which part of the screen we need to parse.
    #       It's probably faster to just label that part.
    im_data, label_array, objs = image_parse.label(im)

    for coord, _ in commands:
        board[coord] = read_hex(im, im_data, label_array, board[coord].image_section)


def run_debug(args):
    board = get_debug_board()
    display_board(board)
    print('\n')
    solutions = list(board.solve())
    board.apply_clicked()
    display_board(board)


def run_screenshot(args):
    board = read_board(PIL.Image.open(args.file))
    display_board(board)
    print('\n')
    solutions = list(board.solve())
    board.apply_clicked()
    display_board(board)


def run_screen(args):
    time.sleep(3)
    im, topleft = screen.grab_game_screen()
    board = read_board(im)

    display_board(board)
    solutions = True
    while solutions and not board.is_solved:
        solutions = list(board.solve())
        apply_commands(board, solutions, topleft)
        print()
        display_board(board)
        print()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    subparsers = parser.add_subparsers()

    debug_parser = subparsers.add_parser('debug', help="")
    debug_parser.set_defaults(func=run_debug)

    screen_parser = subparsers.add_parser('screen', help="")
    screen_parser.set_defaults(func=run_screen)

    screenshot_parser = subparsers.add_parser('screenshot', help="")
    screenshot_parser.add_argument('file', type=str, help="path to the screenshot")
    screenshot_parser.set_defaults(func=run_screenshot)

    args = parser.parse_args()
    args.func(args)
