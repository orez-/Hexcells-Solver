import re
import unittest

import display
from hex_model import Color, Hex, HexBoard


def _get_bump(line):
    # "-" = 0
    # " -" = 0
    # "  -" = 1
    # "   -" = 1
    # "    -" = 0
    # "{3}" = 0
    # " {3}" = 1
    # "  {3}" = 1
    # "   {3}" = 0
    spaces, char = re.match(r"^( *)\S(\S?)", line).groups()
    return bool((len(spaces) + bool(char)) % 4 // 2)


def _board_from_string(string):
    lines = string.split('\n')
    leading_spaces = min(len(re.match(r'^ *', line).group(0)) for line in lines if line.strip())
    lines = [line[leading_spaces:] for line in lines]

    hex_lines = []
    bump = next(_get_bump(line) + i % 2 for i, line in enumerate(lines) if line.rstrip())
    for line in lines:
        line = line.rstrip()
        hex_line = []
        while line:
            spaces, item = re.match(r'^( *)(\S+)', line).groups()
            line = line[len(spaces) + len(item):]
            spaces = len(spaces) // 4
            hex_line += [None] * spaces
            color = Color.black
            if item == '-':
                color = Color.yellow
            elif item == 'x':
                item = '-'
            elif item == 'o':
                item = '-'
                color = Color.blue

            hex_line.append(Hex(item, color))
        hex_lines.append(hex_line)

    board = HexBoard()
    for y, line in enumerate(hex_lines):
        for x, elem in enumerate(line):
            if elem:
                board[x * 2 + ((y % 2) ^ bump), y // 2 - x] = elem

    return board


def _split_on_arrow(board_strings):
    lines = board_strings.split('\n')
    arrow = next(line.index('=>') for line in lines if '=>' in line)
    left_lines = '\n'.join(line[:arrow] for line in lines)
    right_lines = '\n'.join(line[arrow + 2:] for line in lines)
    return left_lines, right_lines


class SolverUnitTest(unittest.TestCase):
    def assertColor(self, coord, expected_color):
        color = self.solved_board[coord].color

        assert color == expected_color, "Found {} at {}, expected {}.\n{}\n\n{}".format(
            color,
            coord,
            expected_color,
            self.original,
            display.display_full_board(self.solved_board),
        )

    def assertSolve(self, start_string, expected_string=None):
        if expected_string is None:
            start_string, expected_string = _split_on_arrow(start_string)
        board = _board_from_string(start_string)
        expected = _board_from_string(expected_string)

        assert set(board._board) == set(expected._board), (
            "Board shapes must match.\n{}\n\n{}".format(
                display.display_full_board(board),
                display.display_full_board(expected),
            )
        )

        list(board.solve())
        board.apply_clicked()

        for coord, hex_ in expected._board.items():
            assert board[coord].color == hex_.color, (
                "Solved board does not match expected.\nExpected:\n{}\n\nActual:\n{}".format(
                    display.display_full_board(expected),
                    display.display_full_board(board),
                )
            )

    def test_noncontiguous_spot(self):
        self.assertSolve("""
           x          x
         -   -      o   -
          -3-   =>   -3-
         x   -      x   -
           -          -
        """)

    def test_noncontiguous_center(self):
        self.assertSolve("""
           -          x
         o   o      o   o
          -3-   =>   -3-
         -   -      -   -
           -          -
        """)

    def test_noncontiguous(self):
        self.assertSolve("""
           o          o
         -   -      x   x
          -2-   =>   -2-
         -   -      -   -
           -          -
        """)

    def test_noncontiguous_edges(self):
        self.assertSolve("""
           -          o
         x   -      x   -
          -3-   =>   -3-
         x   -      x   -
           -          o
        """)

    def test_contiguous_cant_fit(self):
        self.assertSolve("""
           x          x
         -   -      x   -
          {2}   =>   {2}
         x   -      x   o
           -          -
        """)


if __name__ == '__main__':
    unittest.main()
