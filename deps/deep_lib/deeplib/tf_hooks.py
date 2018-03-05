import time

from deeplib.loggers import logger
from deeplib.ml_utils import start_timer, elapsed_time_mins, np_printoptions
from deeplib.stats import StatCounter
from deeplib.tf_utils import simple_value_summary
import tensorflow as tf


class OnOffSessionHook(object):
    def turn_on(self):
        self.active = True

    def turn_off(self):
        self.active = False

    def is_on(self):
        return getattr(self, 'active', True)

    @classmethod
    def turn_all_on(cls, hooks):
        for hook in hooks:
            hook.turn_on()

    @classmethod
    def turn_all_off(cls, hooks):
        for hook in hooks:
            hook.turn_off()


def run_if_hook_on(f):
    def deco(self, *args, **kwargs):
        if self.is_on():
            return f(self, *args, **kwargs)
    return deco


# INFO(maciek): copied from tensorflow examples.
class SummaryHook(tf.train.SessionRunHook, OnOffSessionHook):
    """Logs loss and runtime."""

    def __init__(self, model, all_summaries, global_step_counter, summary_writer, period=40):
        self.model = model
        self.period = period
        self.all_summaries = all_summaries
        self.global_step_counter = global_step_counter
        self.summary_writer = summary_writer

    def set_session(self, sess):
        self.sess = sess

    def _active_step(self):
        if self._step % self.period == 0:
            return True
        else:
            return False

    def begin(self):
        self._step = -1
        self.losses = []
        self._start_time = time.time()

    @run_if_hook_on
    def before_run(self, run_context):
        self._step += 1

        if self._active_step():
            return tf.train.SessionRunArgs(self.all_summaries)
        else:
            return None

    @run_if_hook_on
    def after_run(self, run_context, run_values):
        if self._active_step():
            all_summaries_res = run_values.results
            logger.debug('After run {}, len={}'.format(self._step, len(all_summaries_res)))
            global_step = self.global_step_counter.get()
            logger.info('global_step {} {}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'.format(global_step, self._step))
            self.summary_writer.add_summary(all_summaries_res, global_step=global_step)
            self.summary_writer.flush()
            logger.info('Writing summries')

            # print('loss_all', loss_all)
            #get_neptune_helper().send_num_log('loss_mean', loss_mean)

import collections
ScalarToMonitor = collections.namedtuple('ScalarToMonitor',
                                         ['name', 'tensor', 'aggregate'])

# min_value and max_value could be None
# HistogramSpecs = collections.namedtuple('HistogramSpecs',
#                                       ['buckets', 'min_value', 'max_value'])

HistogramToMonitor = collections.namedtuple('HistogramToMonitor',
                                      ['name', 'tensor'])

import numpy as np
# TODO(maciek): merge it with MySummaryHook somehow
# TODO(maciek): code for showing it somewhere
def is_sorted(l):
    for idx in range(1, len(l)):
        if l[idx - 1] > l[idx]:
            return False
    return True

class HistogramSummaryHook(tf.train.SessionRunHook, OnOffSessionHook):
    """Logs loss and runtime."""

    def __init__(self, model, global_step_counter, send_summary_freq=40, to_monitor=[]):
        '''

        :param model:
        :param global_step_counter:
        :param send_summary_freq:
        :param to_monitor: List of ScalarToMonitor values
        '''
        self.model = model
        self.global_step_counter = global_step_counter
        self.send_summary_freq = send_summary_freq
        self.to_monitor = to_monitor

        self.stats = {}
        for b in to_monitor:
            self.stats[b.name] = StatCounter()

    def begin(self):
        self._step = -1
        self._start_time = time.time()

    def set_summary_writer(self, summary_writer):
        self.summary_writer = summary_writer


    @run_if_hook_on
    def before_run(self, run_context):
        self._step += 1
        return tf.train.SessionRunArgs(list(map(lambda b: b.tensor, self.to_monitor)))  # Asks for loss value.


    @run_if_hook_on
    def after_run(self, run_context, run_values):
        for idx, b in enumerate(self.to_monitor):
            self.stats[b.name].feed_iter(run_values.results[idx])

        if self._step % self.send_summary_freq == 0:
            for idx, b in enumerate(self.to_monitor):
                logger.info(100 * '-')
                all_values = self.stats[b.name].get_values()

                #bins = [0.0, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1e0, 1e1]
                bins = [0.0, 1e-5]
                while bins[-1] < 1:
                    bins.append(bins[-1] * 2.0)
                bins.append(10.0)

                assert(is_sorted(bins))
                hist, bin_edges = np.histogram(all_values,
                                               bins=bins)

                logger.info('histogram for {}'.format(b.name))
                logger.info(hist)
                logger.info(bin_edges)
                logger.info('{} mean {}'.format(b.name, self.stats[b.name].average))

                contrib_left = hist * bin_edges[:-1] / self.stats[b.name].count
                contrib_right = hist * bin_edges[1:] / self.stats[b.name].count

                avg_left = np.sum(contrib_left)
                avg_right = np.sum(contrib_right)

                with np_printoptions(formatter={'float': '{: 0.5f}'.format}, linewidth=10000):
                    print(bin_edges)
                    print(np.asarray(contrib_left))
                    print(np.asarray(contrib_right))
                logger.info('avg_left_ {}'.format(avg_left))
                logger.info('avg_right {}'.format(avg_right))

                # self.summary_writer.add_summary(simple_value_summary(b.name, v),
                #                         global_step=self.global_step_counter.get())
                # self.summary_writer.flush()

            self._reset_stats()

    def _reset_stats(self):
        for stat_name, stat_counter in self.stats.items():
            stat_counter.reset()


# TODO(maciek): we have send_summary_freq, we should also have feed_sumary_freq, or period, sth like that.
class MySummaryHook(tf.train.SessionRunHook, OnOffSessionHook):
    """Logs loss and runtime."""

    def __init__(self, model, global_step_counter, summary_writer, send_summary_freq=40, to_monitor=[]):
        '''

        :param model:
        :param global_step_counter:
        :param send_summary_freq:
        :param to_monitor: List of ToMonitor values
        '''
        self.model = model
        self.global_step_counter = global_step_counter
        self.send_summary_freq = send_summary_freq
        self.to_monitor = to_monitor
        self.summary_writer = summary_writer

        self.stats = {}
        for b in to_monitor:
            self.stats[b.name] = StatCounter()

    def begin(self):
        self._step = -1
        self._start_time = time.time()

    @run_if_hook_on
    def before_run(self, run_context):
        self._step += 1
        return tf.train.SessionRunArgs(list(map(lambda b: b.tensor, self.to_monitor)))  # Asks for loss value.

    @run_if_hook_on
    def after_run(self, run_context, run_values):
        for idx, b in enumerate(self.to_monitor):
            self.stats[b.name].feed(run_values.results[idx])

        if self._step % self.send_summary_freq == 0:
            for idx, b in enumerate(self.to_monitor):
                if b.aggregate == 'mean':
                    v = self.stats[b.name].average
                elif b.aggregate == 'max':
                    v = self.stats[b.name].max
                elif b.aggregate == 'sum':
                    v = self.stats[b.name].sum
                else:
                    raise RuntimeError()

                self.summary_writer.add_summary(simple_value_summary(b.name, v),
                                        global_step=self.global_step_counter.get())
                self.summary_writer.flush()

            self._reset_stats()

    def _reset_stats(self):
        for stat_name, stat_counter in self.stats.items():
            stat_counter.reset()



class RestoreCheckpoint(tf.train.SessionRunHook, OnOffSessionHook):
    def __init__(self, saver, restore_checkpoint):
        self.saver = saver
        self.restore_checkpoint = restore_checkpoint

    def after_create_session(self, session, coord):
        if self.restore_checkpoint is not None:
            logger.info('restoring from {}'.format(self.restore_checkpoint))
            self.saver.restore(session, self.restore_checkpoint)


class SaveModel(tf.train.SessionRunHook, OnOffSessionHook):
    def __init__(self, saver, path, save_frequency_in_minutes):
        self.saver = saver
        self.path = path
        self.save_model_timer = start_timer()
        self.save_frequency_in_minutes = save_frequency_in_minutes
        self.idx = 0

    def after_create_session(self, session, coord):
        self.session = session

    @run_if_hook_on
    def after_run(self, run_values, run_context):
        #print('after_run')
        if elapsed_time_mins(self.save_model_timer) > self.save_frequency_in_minutes or self.idx == 0:
            logger.info('saving model! dir = {}'.format(self.path))
            self.save_model_timer = start_timer()
            self.saver.save(self.session, self.path, global_step=self.idx)
        self.idx += 1



