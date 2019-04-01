import os
from os.path import join as pjoin


model_dir = os.getcwd() + '/static/model'
data_dir = os.getcwd() + '/static/data'
config_dir = os.getcwd() + '/static/configs'
train_dir = os.getcwd() + '/engines/data'


def list_model_dir():
    model_file = pjoin(model_dir, 'model_list')
    model_dict = {}
    if os.path.exists(model_file):
        with open(model_file) as f_:
            for line in f_:
                items = line.strip().split('\t')
                model_dict[(items[0], items[1])] = items[2]
    return model_dict


def get_model_dir(file_data, file_config):
    model_dict = list_model_dir()
    key = (file_data, file_config)
    if key not in model_dict:
        return 'model not found'
    else:
        return model_dict[key]
