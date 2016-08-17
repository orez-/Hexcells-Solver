import collections

import util


def _bfs(im, x, y, predicate):
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


@util.timeit("Beginning fuzzy select")
def fuzzy_select(im, x, y, threshold=15):
    threshold *= 3  # ᖍ(ツ)ᖌ
    rgb = im.getpixel((x, y))

    def predicate(x, y):
        neighbor_rgb = im.getpixel((x, y))
        return sum(abs(a - b) for a, b in zip(rgb, neighbor_rgb)) <= threshold

    return _bfs(im, x, y, predicate)


@util.timeit("Inverting selection")
def invert_selection(im, selection):
    width, height = im.size
    return set((x, y) for x in range(width) for y in range(height) if (x, y) not in selection)


@util.timeit("Getting contiguous sections")
def get_contiguous_sections(im, selection):
    selection = set(selection)

    def predicate(x, y):
        return (x, y) in selection

    while selection:
        x, y = selection.pop()
        result = _bfs(im, x, y, predicate)
        yield result
        selection -= result
