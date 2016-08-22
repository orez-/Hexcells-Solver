import enum
import itertools

import util


class Color(enum.Enum):
    blue = (0x05, 0xa4, 0xeb)
    yellow = (0xff, 0xaf, 0x29)
    black = (0x3e, 0x3e, 0x3e)

    @classmethod
    def closest(cls, value):
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

    Returns (integer value, is_contiguous)
    If the clue indicates the values must be contiguous, `is_contiguous` is True.
    If the clue indicates the values must NOT be contiguous, `is_contiguous` is False.
    If the clue does not indicate whether the values must be contiguous or not,
        `is_contiguous` is None.
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
    def __init__(self, text, color, image_section=None):
        self.value, self.is_contiguous = parse_clue(text)
        self.color = color
        self.image_section = image_section

    @property
    def text(self):
        if self.value is None:
            return '-'
        fmt = {
            None: '{}',
            True: '{{{}}}',
            False: '-{}-',
        }[self.is_contiguous]
        return fmt.format(self.value)

    def clone(self):
        return Hex(self.text, self.color, self.image_section)

    def __repr__(self):
        return '{}({!r}, Color.{})'.format(type(self).__name__, self.text, self.color.name)


def _ordered_neighbors(x_y_z):
    """
    Yield coordinates surrounding the given coordinate, in adjacent order.
    """
    ROTATIONS = 6

    x, y, z = x_y_z
    dx, dy, dz = 1, 0, -1
    for _ in range(ROTATIONS):
        yield x + dx, y + dy, z + dz
        dx, dy, dz = -dy, -dz, -dx


class AbstractContiguousConstraint:
    def __init__(self, contiguous_hexes, value, cycle=False):
        # List of lists of contiguous hexes, in order.
        self._contiguous_hexes = contiguous_hexes
        # Does the final element of the final list connect to the first element of the first list
        self._cycle = cycle
        self.value = value

        self._refactor_cycle()

    def solve(self, board):
        raise NotImplementedError

    def is_done(self, board):
        """
        Find if all hexes this constraint acts upon are uncovered.
        """
        return all(
            board[coord].color != Color.yellow
            for section in self._contiguous_hexes
            for coord in section
        )

    @classmethod
    def ring(cls, board, center):
        center_hex = board[center]

        neighbors = list(_ordered_neighbors(center))
        sections = list(cls._generate_sections(board, neighbors))

        cycle = bool(
            sections and
            sections[0][0] == neighbors[0] and
            sections[-1][-1] == neighbors[-1]
        )

        subcls = ContiguousConstraint if center_hex.is_contiguous else NonContiguousConstraint
        return subcls(
            contiguous_hexes=list(sections),
            value=center_hex.value,
            cycle=cycle,
        )

    @staticmethod
    def _generate_sections(board, hexes):
        """
        Given a list of coordinates, split into contiguous groups.
        """
        def predicate(coord):
            hex_ = board.get(coord)
            return not hex_ or hex_.color == Color.black
        return util.split_iterable(hexes, predicate)

    def _refresh_sections(self, board):
        start = self._contiguous_hexes[0][0]
        end = self._contiguous_hexes[-1][-1]

        self._contiguous_hexes = sum(
            (
                list(self._generate_sections(board, hexes))
                for hexes in self._contiguous_hexes
            ), []
        )

        # Only keep `_cycle` if the start and end are unchanged.
        self._cycle = (
            self._cycle and
            start == self._contiguous_hexes[0][0] and
            end == self._contiguous_hexes[-1][-1]
        )

        self._refactor_cycle()

    def _refactor_cycle(self):
        """
        Cycles are a pain to reason about - remove them when we get the chance.
        """
        if len(self._contiguous_hexes) != 1 and self._cycle:
            end = self._contiguous_hexes.pop()
            self._contiguous_hexes[0] = end + self._contiguous_hexes[0]
            self._cycle = False


class ContiguousConstraint(AbstractContiguousConstraint):
    # Helper methods may assume _contiguous_hexes is accurate, but if
    # they make changes they must clean up after themselves.
    def solve(self, board):
        functions = [
            self._prune_sections,
            self._solve_section,
        ]

        self._refresh_sections(board)
        for fn in functions:
            yield from fn(board)

    def _set_sections(self, sections, color):
        """
        Yield each coordinate in each of the given sections with a color solution.
        """
        yield from ((coord, color) for section in sections for coord in section)

    def _prune_sections(self, board):
        """
        Prune sections known to not contain blue hexes.
        """
        if len(self._contiguous_hexes) <= 1:
            return

        # If we know any blue hexes, prune sections that are not connected.
        for i, section in enumerate(self._contiguous_hexes):
            if any(board[coord].color == Color.blue for coord in section):
                yield from self._set_sections(self._contiguous_hexes[:i], Color.black)
                yield from self._set_sections(self._contiguous_hexes[i + 1:], Color.black)
                self._contiguous_hexes = [section]
                return

        # Prune sections that are too small to accommodate our value.
        to_remove, self._contiguous_hexes = util.partition_if(
            self._contiguous_hexes,
            lambda section: len(section) < self.value
        )
        yield from to_remove

    def _solve_cyclic_section(self, board):
        section, = self._contiguous_hexes
        blues = [i for i, coord in enumerate(section) if board[coord].color == Color.blue]
        if not blues:
            return
        # If we know some blues, we might know the contiguous section wont reach the far side
        # 3: bbyyyy -> bbykky
        possible = set()
        for i, _ in enumerate(section):
            section_range = {j % len(section) for j in range(i, i + self.value)}
            if all(blue in section_range for blue in blues):
                possible |= section_range
        possible = {section[p] for p in possible}

        # Need to be careful with order here - if there's something to remove,
        # we're necessarily no longer cyclical (🙌), but we have to ensure
        # we repair the correct seam; in the following example, we would not
        # want to accidentally return [2, 1] after removing 0s:
        # 1 2 0 0
        # 0 1 2 0
        # 0 0 1 2
        # 2 0 0 1

        # We use `itertools.groupby` to identify up to three groups
        # (the contiguous sections in the examples above), from which
        # we separate to_keep from to_remove while keeping them grouped.
        to_keep = []
        to_remove = []
        for keep, subsection in itertools.groupby(section, lambda coord: coord in possible):
            (to_keep if keep else to_remove).append(list(subsection))

        if to_remove:
            # The only case where we have more than one group to_keep
            # is where it straddles the seam. We reverse any groups
            # to ensure we repair the seam correctly.
            self._contiguous_hexes = [sum(reversed(to_keep), [])]
            self._cycle = False  # 🙌
            yield from self._set_sections(to_remove, Color.black)

    def _solve_noncyclic_section(self, board):
        section, = self._contiguous_hexes
        blues = [i for i, coord in enumerate(section) if board[coord].color == Color.blue]

        # If we know some blues, we might know the contiguous section wont reach the edges.
        # 3: yybbyy -> kybbyk
        if blues:
            max_left = max(0, blues[-1] - self.value + 1)
            min_right = blues[0] + self.value
            temp = list(
                self._set_sections([section[:max_left], section[min_right:]], Color.black)
            )
            yield from temp
            section[:] = section[max_left:min_right]

        # If the area is small enough, we know the center is blue.
        # 4: yyyyy -> ybbby
        new_blues = [
            coord for coord in section[-self.value:self.value]
            if board[coord].color == Color.yellow
        ]
        yield from self._set_sections([new_blues], Color.blue)

        # # Join non-contiguous blues
        # # 5: yybybyy ->
        # # XXX: i can't actually come up with an example of this
        # #      that isn't covered by the above rules!
        # new_blues = [
        #     coord for coord in section[blues[0]:blues[-1]]
        #     if board[coord].color == Color.yellow
        # ]
        # yield from self._set_sections([new_blues], Color.blue)

    def _solve_section(self, board):
        """
        Once there's a single remaining section, analyze it for further solutions.
        """
        if len(self._contiguous_hexes) != 1:
            return

        if self._cycle:
            yield from self._solve_cyclic_section(board)
        else:
            yield from self._solve_noncyclic_section(board)


class NonContiguousConstraint(AbstractContiguousConstraint):
    def solve(self, board):
        pass


class HexBoard:
    def __init__(self):
        self._board = {}
        self._clicked = {}
        self._regions = None
        self._contiguous_constraints = None

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        coord = coordinate_by_key(key)
        clicked = self._clicked.get(coord)
        if clicked:
            return clicked
        return self._board[coord]

    def __setitem__(self, key, value):
        coord = coordinate_by_key(key)
        self._board[coord] = value
        self._clicked.pop(coord, None)

    @property
    def is_solved(self):
        return all(
            self[coord].color != Color.yellow
            for coord in self._board
        )

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
        """
        Unordered set of neighbors to the given coordinate within the given distance.
        """
        return {
            neighbor for neighbor in (
                tuple(map(sum, zip(coord, delta)))
                for delta in generate_hex_circle(distance)
                if any(delta)  # don't yield yourself
            ) if neighbor in self._board
        }

    def _get_simplified_region(self, hexes, value):
        filtered_hexes = set()
        for coord in hexes:
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
        self._contiguous_constraints = set()
        for coord, hex_ in self._board.items():
            if hex_.value is None:
                continue
            if hex_.is_contiguous:
                self._contiguous_constraints.add(AbstractContiguousConstraint.ring(self, coord))
            distance = 1 if hex_.color == Color.black else 2
            hexes, value = self._get_simplified_region(self._neighbors(coord, distance), hex_.value)
            self._regions[hexes] = value

    def _identify_solved_regions(self):
        solutions = set()
        new_regions = {}
        for hexes, value in self._regions.items():
            hexes, value = self._get_simplified_region(hexes, value)
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

    def _click(self, coord, color):
        hex_ = self[coord].clone()
        assert hex_.color == Color.yellow, (coord, hex_, color)
        hex_.color = color
        self._clicked[coord] = hex_

    def solve(self):
        """
        Yield new information that can be inferred from the board state.
        """
        for coord, color in self._solve():
            self._click(coord, color)
            yield coord, color

    def _solve(self):
        self._populate_regions()

        progress = True
        while progress:
            progress = False
            # Identify newly-solved regions
            solutions = True
            while solutions:
                solutions, self._regions = self._identify_solved_regions()
                yield from solutions

            new_regions = self._subdivide_overlapping_regions()
            progress = progress or bool(new_regions)
            self._regions.update(new_regions)

            for constraint in set(self._contiguous_constraints):
                solutions = list(constraint.solve(self))
                progress = progress or bool(solutions)
                yield from solutions
                if constraint.is_done(self):
                    self._contiguous_constraints.remove(constraint)

    def apply_clicked(self):
        for coord, hex_ in self._clicked.items():
            self._board[coord].color = hex_.color
        self._clicked = {}
