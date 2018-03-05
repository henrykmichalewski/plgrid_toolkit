#!/usr/bin/env python
import argparse
import copy
import random
import socket
import string

import os

from deeplib.nemesgenerator import get_random_name

from conf import *


def id_generator(n=10):
   return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(n))

from cmd_pool import execute_cmds
from generate_yaml import generate_experiment_yaml


class LocalRunConfig(object):
    def __init__(self, where, storage_url, neptune_conf_path=None,
                neptune_host=None, neptune_port=None, neptune_username=None, neptune_password=None):
        self.where = where
        self.storage_url = storage_url
        self.neptune_conf_path = neptune_conf_path
        self.neptune_host = neptune_host
        self.neptune_port = neptune_port
        self.neptune_username = neptune_username
        self.neptune_password = neptune_password



class PlgridRunConfig(object):
    # TODO(maciek): refactor venv path
    def __init__(self, where, storage_url, cores=24, run_type='run', partition='plgrid',
                 venv_path=None, neptune_conf_path=None,
                 after_module_load_cmd=None,
                 timelimit='24:00:00', ntasks=1, modules_to_load = [], additional_mrunner_flags=""):
        self.cores = cores
        self.run_type = run_type
        self.partition = partition
        self.where = where
        self.storage_url = storage_url
        self.venv_path = venv_path
        self.neptune_conf_path = neptune_conf_path
        self.after_module_load_cmd = after_module_load_cmd
        self._timelimit = timelimit
        self.ntasks = ntasks
        self.modules_to_load = modules_to_load
        self._additional_mrunner_flags = additional_mrunner_flags

    @property
    def timelimit(self):
        if len(self._timelimit) == 8:
            return self._timelimit
        else:
            s = self._timelimit
            return "{}:{}:{}".format(s[0:2], s[2:4], s[4:6])

    @timelimit.setter
    def timelimit(self, str):
        self._timelimit = str

    def additional_mrunner_flags(self):
      return self._additional_mrunner_flags




class KubernetesRunConfig(object):
    def __init__(self, where, storage_url, netpune_conf_path=None, node_selectors=None, nr_gpus=1, docker_image=None,
                 neptune_host=None, neptune_port=None, neptune_username=None, neptune_password=None):
        self.where = where
        self.storage_url = storage_url
        self.docker_image = docker_image
        self.neptune_conf_path = netpune_conf_path

        if node_selectors:
            assert len(node_selectors) == 1
            self.node_selector_key = node_selectors[0][0]
            self.node_selector_value = node_selectors[0][1]
        else:
            self.node_selector_key = None
            self.node_selector_value = None
        self.nr_gpus = nr_gpus

        self.neptune_host = neptune_host
        self.neptune_port = neptune_port
        self.neptune_username = neptune_username
        self.neptune_password = neptune_password


class Experiment(object):

    def experiments_list(self):
        return [self]

    def additional_mrunner_flags(self):
        return ""

class CmdLineExperiment(Experiment):
    def __init__(self, what, with_yaml, tags, pythonpath, paths_to_dump, name, project_name, parameters):
        self.what = what
        self.tags = tags
        self.pythonpath = pythonpath
        self.paths_to_dump = paths_to_dump
        self.name = name
        self.project_name = project_name
        self.parameters = parameters
        self.with_yaml = with_yaml
        self.random_id = "{}".format(random.randint(100000, 999999))

    def additional_mrunner_flags(self):
        return "--with_yaml" if self.with_yaml else ""

class NeptuneExperiment(Experiment):
    def __init__(self, what, tags, pythonpath, paths_to_dump, name, project_name, parameters):
        self.what = what
        self.tags = tags
        self.pythonpath = pythonpath
        self.paths_to_dump = paths_to_dump
        self.name = name
        self.project_name = project_name
        self.parameters = parameters
        self.random_id = "{}".format(random.randint(100000, 999999))

    def additional_mrunner_flags(self):
        return "--neptune"


class CompositeExperiment(Experiment):
    def __init__(self, experiments_list):
        self._experiments_list = experiments_list
        self.random_id = "{}".format(random.randint(100000, 999999))

        #Subexperiments share the random_id
        for experiment in self._experiments_list:
            experiment.random_id = self.random_id

    def experiments_list(self):
        return self._experiments_list


def run_commands(commands, parallel=1):
    if parallel > 1:
        execute_cmds(commands, num_processes=parallel)
    else:
        for cmd in commands:
            os.system(cmd)
    print('Run {} in total.'.format(len(commands)))


def replace_newlines(str):
    return str.replace('\n', ' ')


def create_mrunner_command_local_neptune(exp, run_config, yaml_path):
    neptune_conf_path = run_config.neptune_conf_path
    print(exp.tags)
    return replace_newlines('''
        {mrunner_local_cli}
        --neptune 
        --storage_url {storage_url}
        {neptune_creds_str}
        {neptune_conf}
        --paths_to_dump {paths_to_dump} 
        --pythonpath {pythonpath}
        --tags {tags} 
        --config {config} 
        -- 
        python {command} 
        '''.format(
        mrunner_local_cli='mrunner_local',
        neptune_conf=(('--neptune_conf {neptune_conf_path}'.format(neptune_conf_path=neptune_conf_path))
                      if neptune_conf_path is not None else ''),
        neptune_creds_str=create_neptune_creds_str(run_config.neptune_host, run_config.neptune_port,
                                                               run_config.neptune_username, run_config.neptune_password),
        pythonpath=exp.pythonpath,
        command=exp.what,
        tags=' '.join(exp.tags),
        storage_url=run_config.storage_url,
        paths_to_dump=exp.paths_to_dump,
        config=yaml_path))

def create_neptune_creds_str(neptune_host, neptune_port, neptune_username, neptune_password):
    return '''
    --neptune_host {neptune_host}
--neptune_port {neptune_port}
--neptune_username {neptune_username}
--neptune_password {neptune_password}
'''.format(neptune_host=neptune_host,
                    neptune_port=neptune_port,
                    neptune_username=neptune_username,
                    neptune_password=neptune_password)

def create_mrunner_command_kube_neptune(exp, run_config, yaml_path):
    node_selector_key_option = ('' if run_config.node_selector_key is None else
                                '--node_selector_key {}'.format(run_config.node_selector_key)
                                )
    node_selector_value_option = ('' if run_config.node_selector_value is None else
                                '--node_selector_value {}'.format(run_config.node_selector_value)
                                )
    return replace_newlines('''
{mrunner_kube_cli}
--neptune
{neptune_creds_str}
--tags {tags}
--docker_image {docker_image}
{node_selector_key_option}
{node_selector_value_option}
--nr_gpus {nr_gpus}
--pythonpath {pythonpath}
--paths_to_dump {paths_to_dump}
--storage_url {storage_url}
--neptune_exp_config {neptune_exp_config} 
--
{command} 
'''.format(
        mrunner_kube_cli='mrunner_kube',
                    node_selector_key_option=node_selector_key_option,
                    node_selector_value_option=node_selector_value_option,
                    neptune_creds_str=create_neptune_creds_str(run_config.neptune_host, run_config.neptune_port,
                                                               run_config.neptune_username, run_config.neptune_password),
                    docker_image=run_config.docker_image,
                   nr_gpus=run_config.nr_gpus,
                   pythonpath=exp.pythonpath,
                   command=exp.what,
                   tags=' '.join(exp.tags),
                   storage_url=run_config.storage_url,
                   paths_to_dump=exp.paths_to_dump,
                   #neptune_conf_path=run_config.neptune_conf_path,
                    neptune_exp_config=yaml_path)
    )



def create_mrunner_command_plgrid(exp, run_config, yaml_path, experiment_id, script_name, modules_to_load_str):
    venv_arg =  '--venv_path {}'.format(run_config.venv_path) if run_config.venv_path is not None else ''



    experiment_additional_flags = exp.additional_mrunner_flags()
    run_config_additional_flags = run_config.additional_mrunner_flags()

    return replace_newlines('''
        {mrunner_plgrid_cli}
        {experiment_additional_flags}
        --config {config}
        --neptune_conf {neptune_conf_path} 
        --partition {partition}
        --{run_type}
        {run_config_additional_flags}
        --cores {cores}
        --ntasks {ntasks}
        --tags {tags}
        --time {timelimit}
        --experiment_id {experiment_id}
        {venv_arg}     
        --pythonpath {pythonpath}
        --paths_to_dump {paths_to_dump}
        --after_module_load_cmd {after_module_load_cmd}
        --storage_url {storage_url}
        --script_name {script_name}
        --modules_to_load {modules_to_load}
        --
        {command} 
        '''.format(
        mrunner_plgrid_cli='mrunner_plgrid',
        experiment_additional_flags = experiment_additional_flags,
        run_config_additional_flags = run_config_additional_flags,
        cores=run_config.cores,
        experiment_id=experiment_id,
                   run_type=run_config.run_type,
                   partition=run_config.partition,
                   pythonpath=exp.pythonpath,
                   command=exp.what,
                   tags=' '.join(exp.tags),
                   timelimit=run_config.timelimit,
                   venv_arg=venv_arg,
                   storage_url=run_config.storage_url,
                   paths_to_dump=exp.paths_to_dump,
                   after_module_load_cmd=run_config.after_module_load_cmd,
                   neptune_conf_path=run_config.neptune_conf_path,
                   config=yaml_path,
                   ntasks=run_config.ntasks,
                   script_name=script_name,
                   modules_to_load=modules_to_load_str))

#### Run Configs ####
host = socket.gethostname()
storage_url = get_storage_url(host)

available_run_configs = {
        'local': LocalRunConfig(where='local', storage_url=storage_url,
                                    neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),
        'local_kdm3': LocalRunConfig(where='local', storage_url=storage_url,
                                     neptune_conf_path='/tmp/plgrid_neptune_kdm3.conf'),

        #### https://kdm3.neptune.deepsense.io ####
        'plgrid_test': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                       run_type='srun', partition='plgrid-testing',
                                       neptune_conf_path='/tmp/plgrid_neptune_kdm3.conf'),

        'plgrid_srun': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='srun',
                                       venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                       neptune_conf_path='/tmp/plgrid_neptune_kdm3.conf'),

        'plgrid_sbatch': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='sbatch',
                                         venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                         neptune_conf_path='/tmp/plgrid_neptune_kdm3.conf'),
        'plgrid_sbatch_a': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='sbatch',
                                         venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                         neptune_conf_path='/tmp/plgrid_neptune_kdm3_a.conf'),


        'plgrid_sbatch_kdm2': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='sbatch',
                                         venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                         neptune_conf_path='/tmp/plgrid_neptune_kdm2.conf'),

        'plgrid_sbatch_kdm2_a': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='sbatch',
                                         venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                         neptune_conf_path='/tmp/plgrid_neptune_kdm2_a.conf'),


        #### neptune.kdm.cyfronet.pl ####
        'plgrid_test_old': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                       run_type='srun', partition='plgrid-testing',
                                       neptune_conf_path='/tmp/plgrid_neptune.conf'),
        'plgrid_srun_old': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='srun',
                                       venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                       neptune_conf_path='/tmp/plgrid_neptune.conf'),

        'plgrid_sbatch_old': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='sbatch',
                                         venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                         neptune_conf_path='/tmp/plgrid_neptune.conf'),

        #### ml.neptune.deepsense.io ####
        'plgrid_test_ml': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                          run_type='srun', partition='plgrid-testing',
                                          venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                          neptune_conf_path='/tmp/ml_neptune.conf'),

        'plgrid_test_ml_osim': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                          run_type='srun', partition='plgrid-testing',
                                          after_module_load_cmd="'export PATH=/net/people/plghenrykm/anaconda2/bin:$PATH ; source activate opensim-rl-2.7'",
                                          neptune_conf_path='/tmp/ml_neptune.conf'),

        'eagle_test_ml_osim': PlgridRunConfig(where='plgrid', storage_url=EAGLE_STORAGE_URL,
                                               run_type='srun', partition='plgrid-testing',
                                               after_module_load_cmd="'export PATH=/home/plgrid/plgtgrel/anaconda2/bin:$PATH ; source activate opensim-rl-2.7'",
                                               neptune_conf_path='/tmp/ml_neptune.conf'),


        'plgrid_srun_ml': PlgridRunConfig(
            where='plgrid', storage_url=PLGRID_STORAGE_URL, run_type='srun',
            venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
            neptune_conf_path='/tmp/ml_neptune.conf'),


'eagle_sbatch_ml_osim_pm': PlgridRunConfig(where='eagle', storage_url=EAGLE_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       after_module_load_cmd="'export ANACONDA_PATH=$HOME/anaconda2osim_v55;export PATH=$ANACONDA_PATH/bin:$PATH; source activate opensim-rl '",
                                                       neptune_conf_path='/tmp/kdmi_pm_neptune.conf'),

'eagle_sbatch_ml_osim_hm': PlgridRunConfig(where='eagle', storage_url=EAGLE_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       after_module_load_cmd="'export ANACONDA_PATH=$HOME/anaconda2osim_v55;export PATH=$ANACONDA_PATH/bin:$PATH; source activate opensim-rl '",
                                                       neptune_conf_path='/tmp/kdmi_hm_neptune.conf'),

# 'eagle_sbatch_ml_osim_pm': PlgridRunConfig(where='eagle', storage_url=EAGLE_STORAGE_URL,
#                                                        run_type='sbatch', partition='plgrid',
#                                                        after_module_load_cmd="'export ANACONDA_PATH=$HOME/anaconda2osim_v50;export PATH=$ANACONDA_PATH/bin:$PATH; source activate opensim-rl ; export LD_LIBRARY_PATH=$ANACONDA_PATH/pkgs/libgcc-4.8.5-2/lib:/home/plgrid/plgtgrel/myglibc/lib'",
#                                                        neptune_conf_path='/tmp/kdmi_pm_neptune.conf'),


    # 'plgrid_sbatch_ml_osim': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
    #                                       run_type='sbatch', partition='plgrid',
    #                                       after_module_load_cmd="'export PATH=/net/people/plghenrykm/anaconda2/bin:$PATH ; source activate opensim-rl-2.7'",
    #                                       neptune_conf_path='/tmp/kdmi_pm_neptune.conf'),

        'plgrid_sbatch_agents': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env',
                                                       neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                                       modules_to_load=["plgrid/tools/python/3.6.0", "plgrid/tools/ffmpeg/3.2.2"]),

    'plgrid_srun_agents': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                            run_type='srun', partition='plgrid',
                                            venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env',
                                            neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                            modules_to_load=["plgrid/tools/python/3.6.0", "plgrid/tools/ffmpeg/3.2.2" ]),

  'plgrid_srun_gpu': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                        run_type='srun', partition='plgrid-gpu',
                                        # venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env',
                                        after_module_load_cmd="'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/net/people/plghenrykm/ppo_tpu/cuda/lib64/'",
                                        venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env_gpu',
                                        neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                        modules_to_load=["plgrid/tools/python/3.6.0", "plgrid/tools/ffmpeg/3.0", "plgrid/apps/cuda/8.0"],
                                     additional_mrunner_flags="--A rl2algosgpus --gres=gpu"),

  'plgrid_sbatch_gpu': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                     run_type='sbatch', partition='plgrid-gpu',
                                     # venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env',
                                     after_module_load_cmd="'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/net/people/plghenrykm/ppo_tpu/cuda/lib64/'",
                                     venv_path='/net/people/plghenrykm/ppo_tpu/ppo_env_gpu',
                                     neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                     modules_to_load=["plgrid/tools/python/3.6.0", "plgrid/tools/ffmpeg/3.0",
                                                      "plgrid/apps/cuda/8.0"],
                                     additional_mrunner_flags="--A rl2algosgpus --gres=gpu"),

  # 'plgrid_srun_agents': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
  #                                           run_type='srun', partition='plgrid',
  #                                           venv_path='/net/people/plgtgrel/kamil/env/intel_2_tf_intel',
  #                                           neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
  #                                           modules_to_load=["plgrid/tools/python/2.7.13", "plgrid/libs/mkl/2017.0.0", "tools/gcc/6.2.0" ]),

  'plgrid_srun_ml_osim_baselines': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                 run_type='srun', partition='plgrid',
                                                 after_module_load_cmd="'export PATH=/net/archive/groups/plggluna/pmilos/anaconda3/envs/opensim-rl/bin:$PATH ; source activate opensim-rl'",
                                                 neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                                         modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                          "plgrid/tools/python/3.6.0",
                                                                          "plgrid/tools/pro-viz/1.1",
                                                                          "tools/ffmpeg/3.2.2",
                                                                          "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                          "plgrid/tools/imagemagick/6.9.1"]),

        'plgrid_sbatch_ml_osim_baselines': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       after_module_load_cmd="'export PATH=/net/archive/groups/plggluna/pmilos/anaconda3/envs/opensim-rl/bin:$PATH ; source activate opensim-rl'",
                                                       neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                                           modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                            "plgrid/tools/python/3.6.0",
                                                                            "plgrid/tools/pro-viz/1.1",
                                                                            "tools/ffmpeg/3.2.2",
                                                                            "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                            "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_sbatch_ml_osim_video': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       after_module_load_cmd="'export PATH=/net/people/plghenrykm/anaconda2/bin:$PATH ; source activate opensim-rl ; export PYTHONPATH=/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib/python3.6/site-packages/:/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib/python3.5/site-packages/:$PYTHONPATH ; export LD_LIBRARY_PATH=/usr/local/cuda-8.0/lib64/:/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib:$LD_LIBRARY_PATH'",
                                                       neptune_conf_path='/tmp/kdmi_pm_neptune.conf',
                                                       modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                        "plgrid/tools/python/3.6.0",
                                                                        "plgrid/tools/pro-viz/1.1",
                                                                        "tools/ffmpeg/3.2.2",
                                                                        "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                        "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_sbatch_ml_osim_hm': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                             run_type='sbatch', partition='plgrid',
                                             after_module_load_cmd="'export PATH=/net/people/plghenrykm/anaconda2/bin:$PATH ; source activate opensim-rl-2.7'",
                                             neptune_conf_path='/tmp/kdmi_hm_neptune.conf',
                                                modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                 "plgrid/tools/python/3.6.0",
                                                                 "plgrid/tools/pro-viz/1.1",
                                                                 "tools/ffmpeg/3.2.2",
                                                                 "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                 "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_srun_ml_osim_baselines_hm': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                     run_type='srun', partition='plgrid',
                                                     after_module_load_cmd="'export PATH=/net/archive/groups/plggluna/pmilos/anaconda3/envs/opensim-rl/bin:$PATH ; source activate opensim-rl'",
                                                     neptune_conf_path='/tmp/kdmi_hm_neptune.conf',
                                                        modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                         "plgrid/tools/python/3.6.0",
                                                                         "plgrid/tools/pro-viz/1.1",
                                                                         "tools/ffmpeg/3.2.2",
                                                                         "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                         "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_sbatch_ml_osim_baselines_hm': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                       run_type='sbatch', partition='plgrid',
                                                       after_module_load_cmd="'export PATH=/net/archive/groups/plggluna/pmilos/anaconda3/envs/opensim-rl/bin:$PATH ; source activate opensim-rl'",
                                                       neptune_conf_path='/tmp/kdmi_hm_neptune.conf',
                                                          modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                           "plgrid/tools/python/3.6.0",
                                                                           "plgrid/tools/pro-viz/1.1",
                                                                           "tools/ffmpeg/3.2.2",
                                                                           "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                           "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_sbatch_ml_osim_video_hm': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                                   run_type='sbatch', partition='plgrid',
                                                   after_module_load_cmd="'export PATH=/net/people/plghenrykm/anaconda2/bin:$PATH ; source activate opensim-rl ; export PYTHONPATH=/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib/python3.6/site-packages/:/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib/python3.5/site-packages/:$PYTHONPATH ; export LD_LIBRARY_PATH=/usr/local/cuda-8.0/lib64/:/net/people/plghenrykm/anaconda2/envs/opensim-rl/lib:$LD_LIBRARY_PATH'",
                                                   neptune_conf_path='/tmp/kdmi_hm_neptune.conf',
                                                      modules_to_load=["openmpi/1.10.2-1_gcc463",
                                                                       "plgrid/tools/python/3.6.0",
                                                                       "plgrid/tools/pro-viz/1.1",
                                                                       "tools/ffmpeg/3.2.2",
                                                                       "plgrid/tools/openmpi/1.6.5-gcc-4.9.2",
                                                                       "plgrid/tools/imagemagick/6.9.1"]),

    'plgrid_sbatch_ml': PlgridRunConfig(where='plgrid', storage_url=PLGRID_STORAGE_URL,
                                            run_type='sbatch',
                                            venv_path='/net/people/plghenrykm/maciek/venvs/modular_rl2_neptune_1.6/',
                                            neptune_conf_path='/tmp/ml_neptune.conf'),

        'kube': KubernetesRunConfig(where='kube', storage_url=storage_url,
                                    neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),

        'kube_cpascal': KubernetesRunConfig(where='kube', storage_url=storage_url,
                                            node_selectors=[('kubernetes.io/hostname', 'pascal-tower02.intra.codilime.com')],
                                    neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),

        'kube_tower01': KubernetesRunConfig(where='kube', storage_url='/mnt/mhome/kube_tests/',
                                            node_selectors=[('kubernetes.io/hostname', 'pascal-tower02.intra.codilime.com')],
                                            neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),

        'kube_tower02': KubernetesRunConfig(where='kube', storage_url='/mnt/mhome/kube_tests/',
                                            node_selectors=[('kubernetes.io/hostname', 'pascal-tower02.intra.codilime.com')],
                                            neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),

        'kube_nonpersonal': KubernetesRunConfig(where='kube', storage_url='/mnt/mhome/kube_tests/',
                                            node_selectors=[('deepsense.ai/personal', 'False')],
                                            neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='maciej.klimek@codilime.com',
                                    neptune_password='gRsWXTDnifOA2RXHn'),

        'kube_pm': KubernetesRunConfig(where='kube', storage_url='/mnt/ml-team/rl/kubernetes_storage/',
                                    neptune_host='ml.neptune.deepsense.io',
                                    neptune_port='443',
                                    neptune_username='piotr.milos@codilime.com',
                                    neptune_password='plosos2n'),
    }


def get_multiple_confg_element(str, index):
    if str == None:
        return None

    elements = str.split(":")
    i = min(index, len(elements)-1)
    return elements[i]


def generate_run_configs(args):
    fields = ['cores', 'partition', 'timelimit', 'docker_image', 'nr_gpus', 'ntasks']


    run_configs = []
    #create 10 running configs for the composite
    for x in range(10):
        r_conf = copy.deepcopy(available_run_configs[get_multiple_confg_element(args.runcfg, x)])
        run_configs.append(r_conf)

        for field in fields:
            val = get_multiple_confg_element(getattr(args, field), x)
            if val != None and hasattr(r_conf, field):
                setattr(r_conf, field, val)


    # print("pm:Run configs:{}".format(run_configs))

    return run_configs


if __name__ == "__main__":
    global run_configs

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter, fromfile_prefix_chars='@')
    parser.add_argument("--ex", required=True)
    parser.add_argument("--docker_image", type=str)
    parser.add_argument("--spec", default='specifications')
    parser.add_argument("--dry_run", dest='dry_run', action='store_true')
    parser.add_argument("--shuffle", dest='shuffle', action='store_true')

    # parser.add_argument("--add_group_tag", action='store_true')
    # parser.add_argument("--add_job_tag", action='store_true')

    parser.add_argument("--runcfg", default='local')
    parser.add_argument("--partition", default=None)
    parser.add_argument("--add_tags", default=[], type=str, nargs='+')
    parser.add_argument("--nr_gpus", default='1')
    parser.add_argument("--cores", type=str, default=None)
    parser.add_argument("--ntasks", type=str, default=None)
    parser.add_argument("--limit", type=str, default=None)
    parser.add_argument("--timelimit", default=None) #24:00:00
    parser.add_argument("--parallel", type=int, default=1)

    args = parser.parse_args()
    path = args.ex

    os.system("mkdir -p xxx")
    os.system("find xxx -maxdepth 1 -mmin +10 -type f|xargs rm")

    experiment_file_name = (path.split(".")[-2]).split("/")[-1]

    vars = {}
    exec(open(path).read(), vars)
    f = vars[args.spec]
    list_of_experiments = f()
    # print("PM list of experiments:{}".format(list_of_experiments))
    all_commands = []

    random_group_tag = 'group_tag_{}'.format(get_random_name())

    random_job_tag = 'job_tag_{}'.format(id_generator(7))

    experiment_run_configs = generate_run_configs(args)

    #add indices of run configs
    # experiments_run_config_idx = [experiment.experiments_list() for experiment in list_of_experiments]
    # print("Dupa:{}".format(experiments_run_config_idx))
    experiments_run_config_idx = [list(enumerate(experiment.experiments_list())) for experiment in list_of_experiments]
    #flatten
    experiments_run_config_idx =  [item for sublist in experiments_run_config_idx for item in sublist]

    # print("PM:run tuples:{}".format(experiments_run_config_idx))

    for run_config_idx, experiment in experiments_run_config_idx:

        experiment_run_config = experiment_run_configs[run_config_idx]

        if isinstance(experiment_run_config, LocalRunConfig):
            yaml_path = "xxx/{}.yaml".format(random.randint(100000, 999999))

            generate_experiment_yaml(yaml_path, experiment)
            experiment.tags = experiment.tags + [experiment_file_name] + ['local']
            #if args.add_group_tag:
            experiment.tags += [random_group_tag]
            #if args.add_job_tag:
            experiment.tags += [random_job_tag]

            experiment.tags += args.add_tags

            command = create_mrunner_command_local_neptune(experiment, experiment_run_config, yaml_path)
            all_commands.append(command)

        if isinstance(experiment_run_config, PlgridRunConfig):
            if experiment_run_config.where=='plgrid':
                os.environ['PLGRID_USERNAME']='plghenrykm'
                # os.environ['MRUNNER_SCRATCH_SPACE'] = '/net/scratch/people/plghenrykm/pmilos/mrunner'
                os.environ['MRUNNER_SCRATCH_SPACE'] = '/net/archive/groups/plggatari/scratch'
                os.environ['PLGRID_HOST'] = 'pro.cyfronet.pl'

            if experiment_run_config.where == 'eagle':
                os.environ['PLGRID_USERNAME']='plgtgrel'
                os.environ['MRUNNER_SCRATCH_SPACE'] = '/home/plgrid/plgtgrel/rl/mrunner_scratch'
                os.environ['PLGRID_HOST'] = 'ui.eagle.man.poznan.pl'


            yaml_path = "xxx/{}.yaml".format(random.randint(1000000, 9999999))
            random_id_tag = 'random_tag_{}'.format(id_generator(10))

            generate_experiment_yaml(yaml_path, experiment)
            # experiment.tags = (experiment.tags + [experiment_file_name] + ['plgrid'] +
            #                    ['cores_{}'.format(experiment_run_config.cores)] + [random_id_tag])
            experiment.tags = (experiment.tags + [experiment_file_name] + [experiment_run_config.where])
            experiment.tags += args.add_tags
            #if args.add_group_tag:
            experiment.tags += [random_group_tag]
            #if args.add_job_tag:
            # experiment.tags += [random_job_tag]
            prefix = os.environ.get("MRUNNER_PREFIX", "m")

            script_name = prefix+experiment_file_name[10:]


            modules_to_load_str = ":"
            for module in experiment_run_config.modules_to_load:
                modules_to_load_str += (module+":")

            command = create_mrunner_command_plgrid(experiment,
                                                    experiment_run_config,
                                                    yaml_path,
                                                    experiment.random_id,
                                                    script_name,
                                                    modules_to_load_str)
            all_commands.append(command)

        if isinstance(experiment_run_config, KubernetesRunConfig):
            yaml_path = "xxx/{}.yaml".format(random.randint(100000, 999999))

            generate_experiment_yaml(yaml_path, experiment)
            experiment.tags = (experiment.tags + [experiment_file_name])
            experiment.tags += args.add_tags
            #if args.add_group_tag:
            experiment.tags += [random_group_tag]
            #if args.add_job_tag:
            experiment.tags += [random_job_tag]


            command = create_mrunner_command_kube_neptune(experiment, experiment_run_config, yaml_path)
            all_commands.append(command)


    if args.shuffle:
        random.shuffle(all_commands)

    if args.limit is not None:
        all_commands = all_commands[:int(args.limit)]


    print('all commands:')
    print(50 * '=')
    print(('\n' + 50 * '-' + '\n').join(all_commands))
    print(50 * '=')

    if not args.dry_run:
        run_commands(all_commands, parallel=args.parallel)
    else:
        print('Not running commands, dry_run=True')
        print('Run {} in total.'.format(len(all_commands)))
