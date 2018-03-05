import glob
import os
import time
import json


from deeplib.neptune_connection.api import create_api


def get_git_urls():
  try:
      import git
      path = os.getcwd()

      REMOTE_REPO_LOCATION = "HERE PLEASE PUT THE PREFIX TO YOUR GIT REPOSITORY TO GET CLICKABLE LINKS"
      LOCAL_REPO_LOCATION = path


      repo_1 = git.Repo(LOCAL_REPO_LOCATION)
      sha_1 = repo_1.head.commit.hexsha
      url_1 = REMOTE_REPO_LOCATION + sha_1

      return url_1
  except:
      return "", ""



PROMETHEUS_STR = "plghenrykm@pro.cyfronet.pl"
EAGLE_STR = "plgtgrel@ui.eagle.man.poznan.pl"

def get_host(experiment_dir):
    return PROMETHEUS_STR
    # if "plgtgrel" in experiment_dir:
    #     return  EAGLE_STR
    # if "plggluna" in experiment_dir:
    #     return PROMETHEUS_STR
    # return None

def model_name(num):
    return "model_{0:04d}".format(num)


def model_num_from_file_name(index_file_name):
    # model_0001.index
    core_str = index_file_name[-10:-6]
    return int(core_str)


def _create_api():
    username = os.environ.get("NEPTUNE_USER", "piotr.milos@codilime.com")
    password = os.environ.get("NEPTUNE_PASSWORD", "es5quoo7QuiP9Oph")
    rest_api_url = "https://"+os.environ.get("NEPTUNE_HOST", "kdmi.neptune.deepsense.io")


    print("Neptune credentials are:{}:{}:{}:".format(username, password, rest_api_url))

    # api = create_api(
    #     username= 'henryk.michalewski@codilime.com',
    #     password= 'ca4vaehahx1Jeib8',
    #     rest_api_url= 'https://kdmi.neptune.deepsense.io')
    api = create_api(
        username=username, #'henryk.michalewski@codilime.com',
        password=password, #'ca4vaehahx1Jeib8',
        rest_api_url=rest_api_url) #'https://kdmi.neptune.deepsense.io')
    return api


def get_jobs_ids_by_tag(tags):
    api = _create_api()

    experiments = api.get_experiments(tags=tags, states=["running"])
    job_ids = []
    for e in experiments.experiments:
        if str(e.state) == 'running':
            job = api.get_experiment_jobs(e.id).jobs[0]
            job_ids.append(job.id)
            # api.jobs_job_id_abort_post(job.id, x_neptune_user_role='normal_user')
        # api.trash_experiments([e.id], x_neptune_user_role='normal_user')
    return job_ids


def clean_jobs_by_tag(tags):
    api = _create_api()

    experiments = api.get_experiments(tags=tags, states=["running"])

    for e in experiments.experiments:
        if str(e.state) == 'running':
            job = api.get_experiment_jobs(e.id).jobs[0]
            print(job.id)
            api.jobs_job_id_abort_post(job.id, x_neptune_user_role='normal_user')
        api.trash_experiments([e.id], x_neptune_user_role='normal_user')

def clean_job_by_id(job_id):
    api = _create_api()
    api.jobs_job_id_abort_post(job_id, x_neptune_user_role='normal_user')



def retrieve_metadata_from_kdmi_neptune(job_id):
    t = 1
    while True:
        try:
            return _retrieve_metadata_from_kdmi_neptune(job_id)
        except Exception as e:
            print("Neptune error:{}".format(e))
        print("Sleeping for:{}".format(t))
        time.sleep(t)
        t+=1


def _retrieve_metadata_from_kdmi_neptune(job_id):
    api = _create_api()
    meta_data = {}
    neptune_job = api.jobs_job_id_get(job_id)
    # print("Neptune job storage:{}".format(neptune_job.storage_location))
    meta_data["Name"] = neptune_job.name
    meta_data["storage_location"] = neptune_job.storage_location

    debug_channel_id = None
    for channel_data in neptune_job.channels:
        if channel_data.name == 'Debugs':
            debug_channel_id = channel_data.id

    if debug_channel_id is not None:
        values = api.get_channel_values(neptune_job.id, debug_channel_id, limit=2000).values
        for point in values:
            x = point.y.text_value.split(":")
            # print(x)
            if len(x) == 2:
                meta_data[x[0]] = x[1]

    hyper_parameters = {}
    meta_data["hyper_parameters"] = hyper_parameters

    for param in neptune_job.parameters:
        hyper_parameters[param.name] = param.default_value

    meta_data["Tags"] = neptune_job.tags

    return meta_data


def get_path_to_model(spec_str):
    if spec_str.startswith("neptune:"):
        kwargs = {'protocol': "neptune"}
        tokens = spec_str.split(":")
        kwargs['epoch'] = int(tokens[-1])
        kwargs['neptune_id'] = tokens[-2][-36:]
        return _get_path_to_model(**kwargs)

    # if spec_str.startswith("neptune_lazy:"):
    #     kwargs = {'protocol': "neptune_lazy"}
    #     tokens = spec_str.split(":")
    #     kwargs['epoch'] = int(tokens[-1])
    #     kwargs['neptune_id'] = tokens[-2][-36:]
    #
    #     return _get_path_to_model(**kwargs)
    if spec_str.startswith("file:"):
        kwargs = {'protocol': "file", "file_name": spec_str.split(":")[1]}
        return _get_path_to_model(**kwargs)

    if spec_str.startswith("dir:"):
        kwargs = {'protocol': "dir", "dir": spec_str.split(":")[1], "epoch":spec_str.split(":")[2]}
        return _get_path_to_model(**kwargs)


    raise NotImplementedError("If you need something do it man! {}".format(spec_str))


def _get_path_to_model(protocol=None, **kwargs):
    if protocol == "file":
        return kwargs["file_name"]
    models_dir_path = None
    model_num = None
    experiment_dir = None
    if protocol == 'dir':
        experiment_dir = kwargs['dir']
        model_num = int(kwargs['epoch'])
        models_dir_path = os.path.join(experiment_dir, "models")
        print("PM Degug1:{} and {}".format(experiment_dir, model_num))
    if "neptune" in protocol:
        neptune_job_id = kwargs["neptune_id"]
        meta_data = retrieve_metadata_from_kdmi_neptune(neptune_job_id)
        experiment_dir = meta_data["Job_dir"]
        models_dir_path = os.path.join(experiment_dir, "models")
        model_num = kwargs['epoch']
        # if protocol=="neptune_lazy":
        #     return "dir:{path}:{epoch}".format(path=models_dir_path, epoch=kwargs["epoch"])

    my_location = os.environ.get("SLURM_CLUSTER_NAME", "local")
    model_location = "local"
    if "plgtgrel" in experiment_dir:
        model_location = "eagle"
    if "plggluna" in experiment_dir:
        model_location = "prometheus"

    if my_location == model_location:
        return _get_path_to_model_local(models_dir_path, model_num)

    if my_location != model_location:
        return _get_path_to_model_transport(model_location, models_dir_path, model_num)

def _get_path_to_model_transport(model_location, models_dir_path, model_num):
    downloader = False
    try:
        from mpi4py import MPI
        downloader = (MPI.COMM_WORLD.Get_rank() == 0)
    except:
        downloader = True

    if downloader:
        print("Downloading model")
        host = None
        if model_location == "prometheus":
            host = PROMETHEUS_STR
        if model_location == "eagle":
            host = EAGLE_STR

        if model_num == -1:
            cmd = "ssh {host} ls {models_dir_path}|tail -n 1".format(host=host, models_dir_path=models_dir_path)
            ret = os.popen(cmd).read()
            # ret = "model_0913.meta"
            print("AAA:{}".format(ret))
            print("BBB.{}".format(ret[6:10]))
            model_num = int(ret[6:10])  #Herdcoded format!!!

        download_cmd = "scp {host}:{models_dir_path}/*{model_num}* .".format(host=host, models_dir_path=models_dir_path,
                                                                            model_num=model_num)
        os.system(download_cmd)
        with open("download_completed.txt", "w+") as f:
            json.dump(model_num, f)
    else:
        while True:
            if os.path.isfile("download_completed.txt"):
                break
            print("Waiting for model to download")
            time.sleep(10)

        time.sleep(10)
        with open("download_completed.txt", "r") as f:
            model_num = json.load(f)

    return os.path.join(os.getcwd(), model_name(model_num))

def _get_path_to_model_local(models_dir_path, model_num):
    print("PM Degug2:{} and {}".format(models_dir_path, model_num))
    if model_num == -1:
        search_path = os.path.join(models_dir_path, "*.index")
        list_of_models = glob.glob(search_path)
        if len(list_of_models) == 0:
            print("No model found on the path")
        last_file = sorted(glob.glob(search_path))[-1]
        # print(last_file)
        model_num = model_num_from_file_name(last_file)

    return os.path.join(models_dir_path, model_name(model_num))
