import collections
import heapq

import hex_model


af = '\x1b[38;5;{}m'.format
ab = '\x1b[48;5;{}m'.format
clear = '\x1b[0m'

hexagon_colors = {
    hex_model.Color.blue: 38,
    hex_model.Color.yellow: 214,
    hex_model.Color.black: 237,
}


def display_board(board):
    """
    Display the board of flat-top hexes.
    """
    string_builder = collections.deque()
    print_ = string_builder.append
    leftmost = board.leftmost
    last_row_num, _ = next(board.rows)
    if board.remaining is not None:
        print_("Remaining: {}\n".format(board.remaining))
    for row_num, row in board.rows:
        print_('\n' * (row_num - last_row_num - 1))
        last_row_num = row_num
        bump = (row_num % 2) != (leftmost % 2)
        last = leftmost
        if bump:
            # leftmost is even, align even x's on left
            # leftmost is odd, align odd x's on left
            print_('  ')
        else:
            # row_num is odd, leftmost is odd, diff one more than you are
            # row_num is even, leftmost is even, diff one more than you are
            last -= 1
        for (x, y, z), hex_ in row:
            color = hexagon_colors[hex_.color]
            color = af(color)
            if x == y == z == 0:
                color += ab(237)
            print_('    ' * ((x - last + 1) // 2 - 1))
            print_('{}{:^3}{} '.format(color, hex_.text, clear))
            last = x
        print_('\n')
    return ''.join(string_builder)


def _draw_mid_row(row_queue, leftmost):
    string_builder = collections.deque()
    print_ = string_builder.append
    last = leftmost - 1
    for (x, y, z), hex_ in heapq.merge(*row_queue, key=lambda x_y_z__hex: x_y_z__hex[0][0]):
        color = hexagon_colors[hex_.color]
        color = ab(color)
        print_('    ' * (x - last - 1))
        print_(' {}   {}'.format(color, clear))
        last = x
    print_('\n')
    return ''.join(string_builder)


def display_full_board(board):
    string_builder = collections.deque()
    print_ = string_builder.append
    leftmost = board.leftmost

    if board.remaining is not None:
        print_("Remaining: {}\n".format(board.remaining))

    row_queue = collections.deque([[], []], 2)
    last_row_num, _ = next(board.rows)

    for row_num, row in board.rows:
        row_diff = (row_num - last_row_num - 1)
        if row_diff > 0:
            row_queue.append([])
            print_(_draw_mid_row(row_queue, leftmost))
            print_('\n\n' * ((row_diff - 1)) + '\n')
        last_row_num = row_num
        row = list(row)

        row_queue.append(row)
        print_(_draw_mid_row(row_queue, leftmost))

        bump = (row_num % 2) != (leftmost % 2)
        last = leftmost

        if bump:
            # leftmost is even, align even x's on left
            # leftmost is odd, align odd x's on left
            print_('    ')
        else:
            # row_num is odd, leftmost is odd, diff one more than you are
            # row_num is even, leftmost is even, diff one more than you are
            last -= 1

        for (x, y, z), hex_ in row:
            color = hexagon_colors[hex_.color]
            color = ab(color)
            print_('        ' * ((x - last + 1) // 2 - 1))
            inner = '{:^3}'.format(hex_.text)
            if x == y == z == 0:
                inner = '{}{}{}'.format(ab(1), inner, color)
            print_('{} {} {}   '.format(color, inner, clear))
            last = x
        print_('\n')
    row_queue.append([])
    print_(_draw_mid_row(row_queue, leftmost))
    return ''.join(string_builder)
