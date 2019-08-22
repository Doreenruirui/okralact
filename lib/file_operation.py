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
                model_dict[tuple(items[:-1])] = items[-1]
    return model_dict

def get_model_dir(file_data, file_config):
    model_dict = list_model_dir()
    key = (file_data, file_config)
    if key not in model_dict:
        return ''
    else:
        return model_dict[key]

def get_model_info(model_dir):
    model_dict = list_model_dir()
    for ele in model_dict:
        if model_dict[ele] == model_dir:
            return ele
    raise 'model not found'

def get_models():
    model_dict = list_model_dir()
    return [model_dict[ele] for  ele  in  model_dict]

def get_files():
    files_list = os.listdir(data_dir)
    return files_list


def get_configs():
    configs_list = os.listdir(config_dir)
    return configs_list


def get_engines():
    return ["kraken", "ocropus", "tesseract", "calamari"]


def rename_file(filename, postfix, files_list):
    if filename + postfix in files_list:
        i = 0
        newname = filename + '_%d%s' % (i, postfix)
        while newname in files_list:
            i += 1
            newname = filename + '_%d%s' % (i, postfix)
        filename = newname
    else:
        filename = filename + postfix
    return filename


def read_list(filename):
    dict_res = {}
    if os.path.exists(filename):
        with open(filename) as f_:
            for line in f_:
                items = line.strip().split('\t')
                key = tuple(items[:-1])
                dict_res[key] = items[-1]
    return dict_res

def write_list(filename, dict_res):
    with open(filename, 'w') as f_:
        for key in dict_res:
            f_.write('\t'.join(key) + '\t' + dict_res[key] + '\n')
