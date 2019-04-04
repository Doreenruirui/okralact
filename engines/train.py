### Todo: Show all the help info

# from parameters import get_parser
from engines.validate_parameters import read_json
from engines.parameters_translator import Translate
import subprocess
from os.path import join as pjoin
import os
import uuid
import tarfile
import shutil
from lib.file_operation import list_model_dir


def clear_data():
    list_files = os.listdir(pjoin(os.getcwd(), 'engines/data'))
    if len(list_files) != 0:
        subprocess.run('rm -r engines/data/*', shell=True)


# def train_from_file(config_file):
#     configs = Config(config_file)
#     cur_folder = os.getcwd()
#     configs.model_dir = pjoin(cur_folder, configs.model_dir)
#     configs.data_dir = pjoin(cur_folder, configs.data_dir)
#     train(configs)
# check whether the data folder contain valid data
# 1. check whether there are images in the folder
# 2. check whether every image has a groundtruth manual transcription
# 3. check whether there is a valid config file
# error code: 0 -- no error
#             1 -- image without transcription
#             2 -- no image in the folder
#             3 -- configure file not found
#             4 -- configure file not valid
def check_data(data_folder):
    list_file = os.listdir(data_folder)
    flag_empty = 1
    for fn in list_file:
        if fn.endswith('.png'):
            prefix = fn.rsplit('.', 1)[0]
            if not os.path.exists(pjoin(data_folder, prefix + '.gt.txt')):
                return 1
            if flag_empty:
                flag_empty = 0
    if flag_empty:
        return 2
    if not os.path.exists(pjoin(data_folder, 'config.txt')):
        return 3
    return 0


def extract_file(filename):
    with tarfile.open(filename, 'r:gz') as _tar:
        for tarinfo in _tar:
            if tarinfo.isdir():
                continue
            fn = tarinfo.name.split('/')[1]
            if fn.startswith('.'):
                continue
            if fn.endswith('.png') or tarinfo.name.endswith('.txt'):
                tarinfo.name = fn
                _tar.extract(tarinfo, 'engines/data')


def add_model(file_data, file_config):
    root_dir = os.getcwd()
    model_file = pjoin(root_dir, 'static/model', 'model_list')
    model_dict = list_model_dir()
    key = (file_data, file_config)
    if key not in model_dict:
        uni_model_dir = uuid.uuid4().hex
        model_dict[key] = uni_model_dir
        model_dir = pjoin(root_dir, 'static/model/', uni_model_dir)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        with open(model_file, 'w') as f_:
            for ele in model_dict:
                f_.write('%s\t%s\t%s\n' % (ele[0], ele[1], model_dict[ele]))
    else:
        model_dir = pjoin(root_dir, 'static/model/', model_dict[key])
        if os.listdir(model_dir):
            shutil.rmtree(model_dir)
        else:
            os.removedirs(model_dir)
        uni_model_dir = uuid.uuid4().hex
        model_dict[key] = uni_model_dir
        model_dir = pjoin(root_dir, 'static/model/', uni_model_dir)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        with open(model_file, 'w') as f_:
            for ele in model_dict:
                f_.write('%s\t%s\t%s\n' % (ele[0], ele[1], model_dict[ele]))
    return model_dir


def train_from_file(file_data, file_config):
    clear_data()
    root_dir = os.getcwd()
    print(root_dir)
    extract_file(pjoin(root_dir, 'static/data', file_data))
    err = check_data(pjoin(root_dir, 'engines/data'))
    print(err)
    if not err:
        configs = read_json(pjoin(root_dir, 'static/configs', file_config))
        print(configs)
        model_dir = add_model(file_data, file_config)
        translator = Translate(configs, model_dir)
        cmd_list = translator.cmd_list
        cmd = '\n'.join(cmd_list)
        print(cmd)
        subprocess.run(cmd, shell=True)


# train_from_file((sys.argv[1], sys.argv[2]))



