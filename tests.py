import unittest

import display
from hex_model import Color, Hex, HexBoard


class SolverUnitTest(unittest.TestCase):
    def assertColor(self, coord, expected_color):
        color = self.solved_board[coord].color

        assert color == expected_color, 'Found {} at {}, expected {}.\n{}\n\n{}'.format(
            color,
            coord,
            expected_color,
            self.original,
            display.display_full_board(self.solved_board),
        )

    def test_noncontiguous_spot(self):
        """
           x          x
         -   -      o   -
          -3-   =>   -3-
         x   -      x   -
           -          -
        """
        board = HexBoard()
        board._board = {
            (0, 0, 0): Hex('-3-', Color.black),
            (1, 0, -1): Hex('-', Color.yellow),
            (1, -1, 0): Hex('-', Color.yellow),
            (-1, 0, 1): Hex('-', Color.yellow),
            (0, 1, -1): Hex('-', Color.yellow),
            (-1, 1, 0): Hex('-', Color.black),
            (0, -1, 1): Hex('-', Color.black),
        }

        self.original = display.display_full_board(board)

        list(board.solve())
        board.apply_clicked()
        self.solved_board = board

        self.assertColor((-1, 0, 1), Color.blue)

    def test_noncontiguous_center(self):
        """
           -          x
         o   o      o   o
          -3-   =>   -3-
         -   -      -   -
           -          -
        """
        board = HexBoard()
        board._board = {
            (0, 0, 0): Hex('-3-', Color.black),
            (1, 0, -1): Hex('-', Color.yellow),
            (1, -1, 0): Hex('-', Color.blue),
            (-1, 0, 1): Hex('-', Color.blue),
            (0, 1, -1): Hex('-', Color.yellow),
            (-1, 1, 0): Hex('-', Color.yellow),
            (0, -1, 1): Hex('-', Color.yellow),
        }

        self.original = display.display_full_board(board)

        list(board.solve())
        board.apply_clicked()
        self.solved_board = board

        self.assertColor((0, -1, 1), Color.black)

    def test_noncontiguous(self):
        """
           o          o
         -   -      x   x
          -2-   =>   -2-
         -   -      -   -
           -          -
        """
        board = HexBoard()
        board._board = {
            (0, 0, 0): Hex('-2-', Color.black),
            (1, 0, -1): Hex('-', Color.yellow),
            (1, -1, 0): Hex('-', Color.yellow),
            (-1, 0, 1): Hex('-', Color.yellow),
            (0, 1, -1): Hex('-', Color.yellow),
            (-1, 1, 0): Hex('-', Color.yellow),
            (0, -1, 1): Hex('-', Color.blue),
        }

        self.original = display.display_full_board(board)

        list(board.solve())
        board.apply_clicked()
        self.solved_board = board

        self.assertColor((-1, 0, 1), Color.black)
        self.assertColor((1, -1, 0), Color.black)

    def test_noncontiguous_edges(self):
        """
           -          o
         x   -      x   -
          -3-   =>   -3-
         x   -      x   -
           -          o
        """
        board = HexBoard()
        board._board = {
            (0, 0, 0): Hex('-3-', Color.black),
            (1, 0, -1): Hex('-', Color.yellow),
            (1, -1, 0): Hex('-', Color.yellow),
            (-1, 0, 1): Hex('-', Color.black),
            (0, 1, -1): Hex('-', Color.yellow),
            (-1, 1, 0): Hex('-', Color.black),
            (0, -1, 1): Hex('-', Color.yellow),
        }

        self.original = display.display_full_board(board)

        list(board.solve())
        board.apply_clicked()
        self.solved_board = board

        self.assertColor((0, -1, 1), Color.blue)
        self.assertColor((0, 1, -1), Color.blue)

    def test_contiguous_cant_fit(self):
        """
           x          x
         -   -      x   -
          {2}   =>   {2}
         x   -      x   -
           -          -
        """
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

        self.original = display.display_full_board(board)

        list(board.solve())
        board.apply_clicked()
        self.solved_board = board

        self.assertColor((-1, 0, 1), Color.black)


if __name__ == '__main__':
    unittest.main()
