#This typically will be a proxy to a proper expriment file but in this case it will do all work.

import pickle
import tensorflow as tf
from deepsense import neptune
from time import sleep

from deeplib.neptune_utils import standard_mrunner_main

def prepare_configs_and_run(ctx, args, exp_dir_path):

  #Read config from example_experiment_1.py
  config = pickle.load(open(args.config_path, 'rb'))
  delta = config["delta"]
  print("I got delta = {}".format(delta))


  sleep(240)



def main(_):
  standard_mrunner_main(prepare_configs_and_run)


if __name__ == '__main__':
  tf.app.run()

