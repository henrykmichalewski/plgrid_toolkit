import numpy as np

# INFO(maciek): copied from tensorpack
class StatCounter(object):
    """ A simple counter"""

    def __init__(self):
        self.reset()

    def feed(self, v):
        """
        Args:
            v(float or np.ndarray): has to be the same shape between calls.
        """
        self._values.append(v)

    def feed_iter(self, v_iter):
        for v in v_iter:
            self._values.append(v)

    def reset(self):
        self._values = []

    @property
    def count(self):
        return len(self._values)

    @property
    def average(self):
        assert len(self._values)
        return np.mean(self._values)

    @property
    def sum(self):
        assert len(self._values)
        return np.sum(self._values)

    @property
    def max(self):
        assert len(self._values)
        return max(self._values)

    def get_values(self):
        return self._values



