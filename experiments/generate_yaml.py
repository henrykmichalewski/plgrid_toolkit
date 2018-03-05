import yaml

def generate_exp_name_based_on_parameters(base_exp_name, parameters, paremeters_in_name):
    exp_name = base_exp_name
    if len(paremeters_in_name)>0:
        exp_name += " _"
        for n in paremeters_in_name:
            exp_name += n
            exp_name += "_equals_"
            exp_name += str(parameters[n])
            exp_name += ", "

        exp_name = exp_name[:-2]
        exp_name += "_"
    return exp_name


def generate_experiment_yaml(file_path, exp):
    dict = {}
    dict["name"] = exp.name
    dict["project"] = exp.project_name

    params_list = []
    for p in exp.parameters:
        param_dict = {}
        param_dict["name"] = p
        param_dict["type"] = "string"
        param_dict["required"] = False
        param_dict["default"] = '{}'.format(exp.parameters[p])
        params_list.append(param_dict)

    dict["parameters"] = params_list

    with open(file_path, 'w') as yaml_file:
        yaml.dump(dict, yaml_file, default_flow_style=False)


