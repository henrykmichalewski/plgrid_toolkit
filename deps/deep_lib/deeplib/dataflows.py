from bunch import Bunch

from deps.deep_lib.deeplib.ml_utils import start_timer, elapsed_time_ms


class DataFlow(object):
    def set_name(self, name):
        self.name = name

    def get_name(self):
        if hasattr(self, 'name'):
            return self.name
        else:
            return 'empty_name'

    def get_data(self):
        raise NotImplementedError


import numpy as np
import cv2


# WARN(maciek): copied from tensorpack
class ImageFromFile(DataFlow):
    """ Produce images read from a list of files. """

    def __init__(self, files, channel=3, resize=None):
        """
        Args:
            files (list): list of file paths.
            channel (int): 1 or 3. Will convert grayscale to RGB images if channel==3.
            resize (tuple): (h, w). If given, resize the image.
        """
        assert len(files), "No image files given to ImageFromFile!"
        self.files = files
        self.channel = int(channel)
        self.imread_mode = cv2.IMREAD_GRAYSCALE if self.channel == 1 else cv2.IMREAD_COLOR
        self.resize = resize

    def size(self):
        return len(self.files)

    def get_data(self):
        for f in self.files:
            im = cv2.imread(f, self.imread_mode)
            if self.channel == 3:
                im = im[:, :, ::-1]
            if self.resize is not None:
                im = cv2.resize(im, self.resize[::-1])
            if self.channel == 1:
                im = im[:, :, np.newaxis]
            yield Bunch(img=im, path=f)


class ProxyDataFlow(DataFlow):
    """ Base class for DataFlow that proxies another"""

    def __init__(self, ds):
        """
        Args:
            ds (DataFlow): DataFlow to proxy.
        """
        self.ds = ds

    def reset_state(self):
        """
        Reset state of the proxied DataFlow.
        """
        self.ds.reset_state()

    def get_name(self):
        return self.ds.get_name()

    def size(self):
        return self.ds.size()


# INFO(maciek): copied from tensorpack
class RepeatedData(ProxyDataFlow):
    """ Take data points from another DataFlow and produce them until
        it's exhausted for certain amount of times.
    """

    def __init__(self, ds, nr):
        """
        Args:
            ds (DataFlow): input DataFlow
            nr (int): number of times to repeat ds.
                Set to -1 to repeat ``ds`` infinite times.
        """
        self.nr = nr
        super(RepeatedData, self).__init__(ds)

    def size(self):
        """
        Raises:
            :class:`ValueError` when nr == -1.
        """
        if self.nr == -1:
            raise ValueError("size() is unavailable for infinite dataflow")
        return self.ds.size() * self.nr

    def get_data(self):
        if self.nr == -1:
            while True:
                for dp in self.ds.get_data():
                    yield dp
        else:
            for _ in range(self.nr):
                for dp in self.ds.get_data():
                    yield dp


# INFO(maciek): copied from tensorpack
class FixedSizeData(ProxyDataFlow):
    """ Generate data from another DataFlow, but with a fixed size.
        The state of the underlying DataFlow won't be reset when it's exhausted.
    """

    def __init__(self, ds, size):
        """
        Args:
            ds (DataFlow): input dataflow
            size (int): size
        """
        super(FixedSizeData, self).__init__(ds)
        self._size = int(size)
        self.itr = None

    def size(self):
        return self._size

    def get_data(self):
        if self.itr is None:
            self.itr = self.ds.get_data()
        cnt = 0
        while True:
            try:
                dp = next(self.itr)
            except StopIteration:
                self.itr = self.ds.get_data()
                dp = next(self.itr)

            cnt += 1
            yield dp
            if cnt == self._size:
                return


class RememberData(ProxyDataFlow):
    '''
    It remember whole ds dataflow in first call to get_data, and then reads from this memory in
    subsequent calls.
    This can be useful in debugging a net, something does not work, then you can try to teach the
    net on few examples.
    '''

    def __init__(self, ds):
        super().__init__(ds)
        self.memory = None

    def get_data(self):
        if self.memory is None:
            self.memory = []
            for v in self.ds.get_data():
                self.memory.append(v)
                yield v
        else:
            for v in self.memory:
                yield v


class ApplyFunDataFlow(ProxyDataFlow):
    def __init__(self, ds, fun):
        super().__init__(ds)
        self.fun = fun

    def get_data(self):
        for v in self.ds.get_data():
            vv = self.fun(v)
            yield vv


class AddFieldsDataFlow(ProxyDataFlow):
    def __init__(self, ds, **fields):
        super().__init__(ds)
        self.fields = fields

    def get_data(self):
        for v in self.ds.get_data():
            for key, value in self.fields.items():
                setattr(v, key, value)
            yield v


class AddDictFieldsDataFlow(ProxyDataFlow):
    def __init__(self, ds, **fields):
        super().__init__(ds)
        self.fields = fields

    def get_data(self):
        for v in self.ds.get_data():
            for key, value in self.fields.items():
                assert isinstance(v, dict)
                v[key] = value
            yield v


class BatchData(DataFlow):
    def __init__(self, ds, mb_size, fields):
        self.ds = ds
        self.mb_size = mb_size
        self.fields = fields

    def _collect_mb(self, mb):
        res = Bunch()
        for field in self.fields:
            res_np = np.stack(map(lambda ex: getattr(ex, field), mb))
            res[field + '_np'] = res_np
        return res

    def get_data(self):
        mb = []
        mb_start_timer = start_timer()
        for ex in self.ds.get_data():
            mb.append(ex)
            if len(mb) == self.mb_size:
                mb_elapsed_time_ms = elapsed_time_ms(mb_start_timer)
                res = self._collect_mb(mb)
                res.mb_elapsed_time_ms = mb_elapsed_time_ms
                yield res
                mb = []
                mb_start_timer = start_timer()

        if len(mb):
            res = self._collect_mb(mb)
            res.mb_elapsed_time_ms = elapsed_time_ms(mb_start_timer)
            yield res
