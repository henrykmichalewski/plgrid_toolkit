import copy
import os
import random
import string

from dispatcher import NeptuneExperiment, CompositeExperiment, CmdLineExperiment

import pickle
from munch import Munch as Bunch


def id_generator(n=10):
   return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(n))

class Choose(object):
    def __init__(self, *args):
        if isinstance(args[0], list):
            self.list_val = args[0]
        else:
            self.list_val = args

# TODO(maciek): get rid of this xxx!
def write_extra_config(extra_config, path_prefix='xxx/'):
    extra_config_filepath = os.path.join(path_prefix, id_generator(5) + '.pkl')
    with open(extra_config_filepath, 'wb') as f:
        pickle.dump(extra_config, f)
    return extra_config_filepath

def choose_random(l, n):
    ll = copy.copy(l)
    random.shuffle(ll)
    return ll[:n]


def create_experiments(create_experiment_for_specs_fun, specs, add_all_hparams=True):
    experiment_list = []
    for spec_params in expand_template(specs):
        print(type(spec_params))
        if add_all_hparams:
            kwargs = spec_params
            kwargs.update(all_hparams=spec_params)
            experiment_list.append(create_experiment_for_specs_fun(**kwargs))
        else:
            experiment_list.append(create_experiment_for_specs_fun(**spec_params))
    return experiment_list


def expand_template(template):
    res = [Bunch()]
    for name, value in template.items():
        if isinstance(value, Choose):
            l = value.list_val
        else:
            l = [value]

        new_res = []
        for a in res:
            for v in l:
                new_a = copy.copy(a)
                new_a[name] = v
                new_res.append(new_a)
        res = new_res

    return res


def get_neptune_params_dict(kwargs):
    dict = {}
    for k, v in kwargs.items():
        dict['{}'.format(k)] = v
    return dict


def bridge_spec(core_experiment, kwargs):
    what = 'python learn_to_run/neptune_bridge.py'

    name = core_experiment.name
    project_name = core_experiment.project_name
    pythonpath = '.:deep_lib'
    paths_to_dump = 'learn_to_run deps/deep_lib xxx'
    tags = 'pmilos lean_to_run'.split(' ')

    #These are parameters to display in neptune
    # (they are not passed to the actual experiment)
    parameters = {}
    for k, v in kwargs.items():
        parameters['{}'.format(k)] = v

    return NeptuneExperiment(what=what,
                                name=name,
                                project_name=project_name,
                                tags=tags,
                                pythonpath=pythonpath,
                                parameters=parameters,
                                paths_to_dump=paths_to_dump)


def create_video_spec_from_experiment(experiment):

    what = 'python -u learn_to_run/video_main.py'

    name = experiment.name
    project_name = experiment.project_name
    pythonpath = experiment.pythonpath
    paths_to_dump = experiment.paths_to_dump
    tags = [''] #Not relevant since not in neptune
    parameters = experiment.parameters


    return CmdLineExperiment(what=what,
                             with_yaml=True,
                                name=name,
                                project_name=project_name,
                                tags=tags,
                                pythonpath=pythonpath,
                                parameters=parameters,
                                paths_to_dump=paths_to_dump)




def wrap_experiment_with_bridge_and_video(experiment_fun):

    def wrapped_exp(all_hparams=None, **kwargs):
        core_experiment = experiment_fun(**kwargs)

        bridge = bridge_spec(core_experiment, kwargs)

        video = create_video_spec_from_experiment(core_experiment)

        return CompositeExperiment([bridge, core_experiment, video])

    return wrapped_exp

def wrap_experiment_with_video(experiment_fun):

    def wrapped_exp(all_hparams=None, **kwargs):
        neptune_params_dict = get_neptune_params_dict(kwargs)

        core_experiment = experiment_fun(**kwargs)
        core_experiment.parameters.update(neptune_params_dict)

        video = create_video_spec_from_experiment(core_experiment)

        return CompositeExperiment([core_experiment, video])

    return wrapped_exp