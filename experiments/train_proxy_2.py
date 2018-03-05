#This typically will be a proxy to a proper expriment file but in this case it will do all work.

import pickle
import tensorflow as tf
from deepsense import neptune
from time import sleep
import math


from deeplib.neptune_utils import get_neptune_helper, standard_mrunner_main

def prepare_configs_and_run(ctx, args, exp_dir_path):


  #Read config from example_experiment_1.py
  config = pickle.load(open(args.config_path, 'rb'))
  delta = config["delta"]
  print("I got delta = {}".format(delta))

  neptune_helper = get_neptune_helper()
  neptune_helper.setup_neptune([])
  neptune_helper.send_debug("This is a debug/information message")

  for x in range(1000):
    print("Time step {}".format(x))
    get_neptune_helper().send_num_log("what a cool graph", math.sin(delta*x))
    sleep(1)



def main(_):
  standard_mrunner_main(prepare_configs_and_run)


if __name__ == '__main__':
  tf.app.run()

