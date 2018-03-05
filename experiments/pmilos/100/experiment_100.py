from codilime_utils import get_git_urls
from utils import *


def create_experiment_for_spec(env_name, learning_rate):
    what = 'python experiments/run_atari.py'

    name = 'atari example experiment'
    project_name = "Atari tutorial"

    python_path = '.:deps/deep_lib:deps/baselines'

    paths_to_dump = 'xxx deps experiments'

    tags = 'pmilos tutorial atari'.split(' ')

    config = {
      "env_name" : env_name,
      "learning_rate" : learning_rate
              }

    git_url_1 = get_git_urls()
    config_path = write_extra_config(config)
    parameters = {"config_path": config_path, "git_url_1": git_url_1}
    parameters.update(config)


    return NeptuneExperiment(what=what,
                             name=name,
                             project_name=project_name,
                             tags=tags,
                             pythonpath=python_path,
                             parameters=parameters,
                             paths_to_dump=paths_to_dump)

parameters_spec = Bunch(env_name=Choose(["BreakoutNoFrameskip-v4", "BreakoutNoFrameskip-v4"]),
                        learning_rate=Choose(2.5e-4, 1e-4))


def spec():
    return create_experiments(create_experiment_for_spec, parameters_spec, add_all_hparams=False)