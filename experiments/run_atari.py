#
#
# This is a verion of baselines/ppo2/run_atari.py adopted to our framework
#
#

import sys
from baselines import logger
from baselines.common.cmd_util import make_atari_env, atari_arg_parser
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.ppo2 import ppo2
from baselines.ppo2.policies import CnnPolicy, LstmPolicy, LnLstmPolicy
import multiprocessing
import tensorflow as tf
import pickle
from deeplib.neptune_utils import standard_mrunner_main, get_neptune_helper


#We write a class which sends logs into neptune
class NeptuneLogger(object):

    def __init__(self):
        self.level = logger.INFO
        neptune_helper = get_neptune_helper()
        neptune_helper.setup_neptune([])
        neptune_helper.send_debug("This is a debug/information message")

    def logkv(self, key, val):
        print("Log:{key}={val}".format(key=key, val=val))
        get_neptune_helper().send_num_log(key, val)

    def dumpkvs(self):
        return None

    def log(self, *args, level=logger.INFO):
        if self.level <= level:
            print("Logger:{}".format(args))

    def set_level(self, level):
        self.level = level

    def get_dir(self):
        return None

    def close(self):
        return None



def train(env_id, num_timesteps, seed, policy, learning_rate):

    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin': ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True #pylint: disable=E1101
    tf.Session(config=config).__enter__()

    env = VecFrameStack(make_atari_env(env_id, 8, seed), 4)
    policy = {'cnn' : CnnPolicy, 'lstm' : LstmPolicy, 'lnlstm' : LnLstmPolicy}[policy]
    ppo2.learn(policy=policy, env=env, nsteps=128, nminibatches=4,
        lam=0.95, gamma=0.99, noptepochs=4, log_interval=1,
        ent_coef=.01,
        lr=learning_rate,
        cliprange=lambda f : f * 0.1,
        total_timesteps=int(num_timesteps * 1.1))




def prepare_configs_and_run(ctx, args, exp_dir_path):

  #Read config from example_experiment_1.py
  config = pickle.load(open(args.config_path, 'rb'))
  env = config["env_name"]
  learning_rate = config["learning_rate"]

  # We plug our logger insted OpenAi'one ;)
  ourlogger = logger.Logger.DEFAULT = logger.Logger.CURRENT = NeptuneLogger()

  #It is typically a bad practice to put constants into code!!!!
  seed = 10
  num_timesteps = 10e6
  policy = 'cnn'

  train(env, num_timesteps=num_timesteps, seed=seed, policy=policy, learning_rate=learning_rate)


def main(_):
  standard_mrunner_main(prepare_configs_and_run)


if __name__ == '__main__':
  tf.app.run()
