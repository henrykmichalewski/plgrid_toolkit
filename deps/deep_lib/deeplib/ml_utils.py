import contextlib
import os

import errno

import datetime
import random
import string
import time

import numpy as np
from PIL import ImageFont, Image, ImageDraw
from matplotlib import pyplot as plt

from sim2real import SIM2REAL_ROOT


def mkdir_p(path):
    try:
        os.makedirs(path)
        return path
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return path
        else:
            raise

class StepCounter(object):
    def __init__(self):
        self.v = 0

    def add(self, s=1):
        self.v += s

    def get(self):
        return self.v

def start_timer():
    return time.time()


def elapsed_time_secs(timer):
    return time.time() - timer


def elapsed_time_mins(timer):
    return (time.time() - timer) / 60


def elapsed_time_ms(timer):
    return (time.time() - timer) * 1000


def id_generator(n=10):
   return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(n))


def timestamp_str():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%m_%d_%H_%M_%S')


def timestamp_alt_str():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%y_%m_%d_%H_%M')


def read_file(path):
    with open(path, 'r') as f:
        return '\n'.join(f.readlines())


def write_to_file(path, content):
    with open(path, 'w') as f:
        f.write(content)


FREE_SANS_FONT_PATH = os.path.join(SIM2REAL_ROOT, 'resources/fonts/', 'FreeSans.ttf')
FREE_SANS_FONT = ImageFont.truetype(FREE_SANS_FONT_PATH, 12)


def render_debug_texts(frame, debug_texts, font=FREE_SANS_FONT):
    sx = frame.shape[0] # height equal to fram height
    sy = 400
    a = np.ones([sx, sy, 3]) * 255.0

    a = Image.fromarray(a.astype('uint8'))
    draw = ImageDraw.Draw(a)

    debug_texts = debug_texts[:50]
    # self.debug_texts = ["AAA", "BBB", "CCCC"]
    # print self.debug_texts
    i = 0
    for text in debug_texts:
        draw.text((10, 10 + i * 15), text=text, font=font, fill=(0, 0, 0, 255))
        i += 1
    new_frame = np.concatenate((a, frame), axis=1)
    #frame[visual_debug_height:sx + visual_debug_height, :sy, :] = np.array(a)

    return new_frame


def plot_image_to_file_rgb(img, filepath, interpolation='none'):
    plt.imshow(img, interpolation=interpolation)
    plt.savefig(filepath)
    plt.clf()


def numpy_img_to_PIL(img):
    from PIL import Image
    if img.dtype in ['float32', 'float64']:
        data = np.asarray(img * 255, dtype=np.uint8)
    elif img.dtype in ['int32', 'uint8', 'uint32']:
        data = np.asarray(img, dtype=np.uint8)
    else:
        raise RuntimeError('Unknown dtype ' + str(img.dtype))

    if len(img.shape) == 3 and img.shape[2] == 3:
        im = Image.fromarray(data, 'RGB')
    elif len(img.shape) == 2:
        im = Image.fromarray(data, 'L')
    else:
        raise RuntimeError()
    return im


def plot_image_to_file2(img, filepath, interpolation='none', only_image=True, driver='JPEG'):
    if only_image:
        im = numpy_img_to_PIL(img)
        im.save(filepath)
        return filepath
    else:
        plt.imshow(img, interpolation=interpolation)
        plt.savefig(filepath)
        return filepath

# INFO(maciek): copied from https://stackoverflow.com/questions/2891790/how-to-pretty-printing-a-numpy-array-without-scientific-notation-and-with-given

@contextlib.contextmanager
def np_printoptions(*args, **kwargs):
    '''
    example usage:
    with np_printoptions(formatter={'float': '{: 0.5f}'.format}, linewidth=10000):
        print(bin_edges)
    '''
    original = np.get_printoptions()
    np.set_printoptions(*args, **kwargs)
    try:
        yield
    finally:
        np.set_printoptions(**original)

def as_mb(arr):
    return np.expand_dims(arr, axis=0)