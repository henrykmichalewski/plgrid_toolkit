#!/usr/bin/env bash

#You need to set up correct paths and environment

export PYTHONPATH=$PYTHONPATH:/Users/piotr.milos/PycharmProjects/tensor-2-tensor-with-mrunner/tensor-2-tensor-with-mrunner/deps/tensor2tensor
#Activate environement with all goodies, in particular mrunner. It needs to be python 2.7
source /Users/piotr.milos/PycharmProjects/VirtualEnvs/default_2.7_all/bin/activate

#Put your prefix here
export MRUNNER_PREFIX="p"

set -x

python deepsense_experiments/dispatcher.py --ex $1 --spec spec --runcfg plgrid_srun_agents --cores 24 --limit 1 --partition plgrid --timelimit 010000
