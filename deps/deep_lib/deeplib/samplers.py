import numpy as np


class BaseSampler(object):
    def __init__(self):
        pass

    def sample(self):
        raise NotImplementedError()


class UniformIntIntervalSampler(BaseSampler):
    def __init__(self, low, high, size=()):
        '''
        [low, high)
        :param low:
        :param high:
        :param size:
        '''
        assert isinstance(low, int)
        assert isinstance(high, int)

        self.low = low
        self.high = high
        self.size = size

        super().__init__()

    def sample(self):
        return np.random.randint(self.low, self.high, self.size)


class ConstantSampler(BaseSampler):
    def __init__(self, v):
        self.v = v

    def sample(self):
        return self.v


class ListSampler(BaseSampler):
    def __init__(self, l):
        self.l = l

    def sample(self):
        return self.l[np.random.randint(0, len(self.l))]


class UniformIntervalSampler(BaseSampler):
    def __init__(self, low, high):
        self.low = low
        self.high = high

        super().__init__()

    def sample(self):
        return np.random.uniform(self.low, self.high, ())





