from codilime_utils import get_git_urls
from utils import *


def create_experiment_for_spec(delta):
# def create_experiment_for_spec(delta, gamma):

    what = 'python experiments/train_proxy_2.py'
    name = 'example experiment sine'

    project_name = "tutorial"
    python_path = '.:deps/deep_lib:deps/tensor2tensor'
    paths_to_dump = 'xxx deps experiments'
    tags = 'pmilos tutorial'.split(' ')

    config = {
      "delta" : delta,
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

parameters_spec = Bunch(delta=Choose([0.5, 1.0]))
# parameters_spec = Bunch(delta=Choose([0.5, 1.0]), gamma=Choose(0.1, 0.2))


def spec():
    return create_experiments(create_experiment_for_spec, parameters_spec, add_all_hparams=False)