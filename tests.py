import display
from hex_model import Color, Hex, HexBoard


def test_contiguous_cant_fit():
    board = HexBoard()
    board._board = {
        (0, 0, 0): Hex('{2}', Color.black),
        (1, 0, -1): Hex('-', Color.yellow),
        (1, -1, 0): Hex('-', Color.yellow),
        (-1, 0, 1): Hex('-', Color.yellow),
        (0, 1, -1): Hex('-', Color.yellow),
        (-1, 1, 0): Hex('-', Color.black),
        (0, -1, 1): Hex('-', Color.black),
    }

    original = display.display_full_board(board)

    list(board.solve())
    board.apply_clicked()

    color = board[(-1, 0, 1)].color
    assert color == Color.black, '{} != {}\n{}\n\n{}'.format(
        color,
        Color.blue,
        original,
        display.display_full_board(board),
    )


if __name__ == '__main__':
    test_contiguous_cant_fit()
