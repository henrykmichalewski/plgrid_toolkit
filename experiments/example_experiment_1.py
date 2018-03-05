from codilime_utils import get_git_urls
from utils import *


def create_experiment_for_spec(delta):

    #The file to be run
    what = 'python experiments/train_proxy_1.py'

    #Name in neptune
    name = 'example experiment'

    #project name in neptune
    project_name = "tutorial"

    #this paths are added to pythonpath in the remote experiment
    python_path = '.:deps/deep_lib:deps/tensor2tensor'

    #this paths are send to the plgrid
    paths_to_dump = 'xxx deps experiments'

    #tag dispayed in neptune
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

parameters_spec = Bunch(delta=Choose([0.5]))


def spec():
    return create_experiments(create_experiment_for_spec, parameters_spec, add_all_hparams=False)