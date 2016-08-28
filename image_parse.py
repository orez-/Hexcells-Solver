import collections

import numpy
import pytesseract
import scipy.ndimage

import util


class Box(collections.namedtuple('Box', 'left top right bottom')):
    @classmethod
    def from_slice(cls, slice_):
        ys, xs = slice_
        return cls(xs.start, ys.start, xs.stop, ys.stop)

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    @property
    def center(self):
        return self.left + self.width // 2, self.top + self.height // 2

    @property
    def slice(self):
        return slice(self.top, self.bottom), slice(self.left, self.right)

    @property
    def text_box(self):
        # we chop off the corners of the hex to avoid getting the OCR confused about
        # the shape of the hex vs numbers.
        fourth_width = self.width // 4
        fourth_height = self.height // 4
        return Box(
            left=self.left + fourth_width,
            top=self.top + fourth_height,
            right=self.right - fourth_width,
            bottom=self.bottom - fourth_height,
        )


@util.timeit("Labeling.")
def label(im):
    array = numpy.array(im)
    # Do not group white pixels.
    mask = (array[:, :, 0] < 150) | (array[:, :, 1] < 150) | (array[:, :, 2] < 150)
    label_array, numobjects = scipy.ndimage.label(mask)
    objects = map(Box.from_slice, scipy.ndimage.find_objects(label_array))
    return array, label_array, objects


def debug_labels(label_array):
    import matplotlib.pyplot as plt
    plt.imshow(label_array)
    plt.show()


def get_text_from_image(im):
    """
    Given an image, return the text from it.

    See https://github.com/tesseract-ocr/tesseract/wiki/Command-Line-Usage
    for options + explanations.
    """
    # TODO: read from a numpy array instead of a PIL image.
    im = im.convert('L')  # convert to grayscale for better readability
    config = '-psm 8 -c tessedit_char_whitelist=0123456789-?{}'
    return pytesseract.image_to_string(im, config=config)
