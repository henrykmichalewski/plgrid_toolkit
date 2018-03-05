#!/usr/bin/env bash

#You need to activate your mrunner environment
source /Users/piotr.milos/PycharmProjects/VirtualEnvs/default_2.7_all/bin/activate

#Possibly set PYTHONPATH
#export PYTHONPATH=$PYTHONPATH:/Users/piotr.milos/PycharmProjects/tensor-2-tensor-with-mrunner/tensor-2-tensor-with-mrunner/deps/tensor2tensor

#Put your initials here
export MRUNNER_PREFIX="pm"

set -x

python experiments/dispatcher.py --ex $1 --spec spec --runcfg plgrid_srun_gpu --cores 4 --limit 1 --timelimit 010000
