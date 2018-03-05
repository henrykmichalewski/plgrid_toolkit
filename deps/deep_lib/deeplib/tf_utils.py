import tensorflow as tf
from tensorflow.core.framework import summary_pb2

from sim2real.loggers import logger


def add_variable_summaries(var):
    """Attach a lot of summaries to a Tensor (for TensorBoard visualization)."""
    def transform_var_name(name):
        return name.replace('/', ' ').replace(':', ' ').replace(' ', '-')
    logger.info('add_variable_summaries {}, {}'.format(var.name, transform_var_name(var.name)))
    with tf.name_scope('summaries' + '_' + transform_var_name(var.name)):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.summary.scalar('stddev', stddev)
        tf.summary.scalar('max', tf.reduce_max(var))
        tf.summary.scalar('min', tf.reduce_min(var))
        tf.summary.histogram('histogram', var)


# def add_activation_summary(res):
#     logger.info('add_activation_summary')
#
#     with tf.name_scope('acc_summaries'):
#         mean = tf.reduce_mean(res)
#         tf.summary.scalar('mean', mean)
#         with tf.name_scope('stddev'):
#             stddev = tf.sqrt(tf.reduce_mean(tf.square(res - mean)))
#         tf.summary.scalar('stddev', stddev)
#         tf.summary.scalar('max', tf.reduce_max(res))
#         tf.summary.scalar('min', tf.reduce_min(res))
#         tf.summary.histogram('histogram', res)
#     return res

# def maciek_scalar_summary(name, t):

ACTIVATION_SUMMARY_COLLECTION = 'activation_summary_collection'

def analyze_tf_summaries(summary_res):
    if isinstance(summary_res, bytes):
        summ = summary_pb2.Summary()
        summ.ParseFromString(summary_res)
        summary = summ
        for value in summary.value:
            field = value.WhichOneof('value')
            if field == 'simple_value':
                print('summary {}, {}'.format(value.tag, value.simple_value))

def add_activation_summary(t, name=''):
    mean = tf.reduce_mean(t)
    nonzero_frac = 1 - tf.nn.zero_fraction(t)

    tf.summary.scalar('{}-activation-mean'.format(name), mean, collections=[ACTIVATION_SUMMARY_COLLECTION])
    tf.summary.scalar('{}-activation-nonzero-frac'.format(name), nonzero_frac, collections=[ACTIVATION_SUMMARY_COLLECTION])
    return t


def simple_value_summary(name, value):
    summary = tf.Summary()
    summary.value.add(tag=name, simple_value=value)
    return summary



