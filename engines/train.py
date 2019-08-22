from engines.translate_parameters import Translate
import subprocess
from os.path import join as pjoin
import os
import uuid
import shutil
from lib.file_operation import list_model_dir
from engines.common import extract_file, clear_data
from engines import data_folder, tmp_folder
from engines.valid import valid_from_file


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


def add_model(file_data, file_config):
    root_dir = os.getcwd()
    model_file = pjoin(root_dir, 'static/model', 'model_list')
    model_dict = list_model_dir()
    print(model_dict)
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
    clear_data(data_folder)
    clear_data(tmp_folder)
    root_dir = os.getcwd()
    print(root_dir)
    extract_file(pjoin(root_dir, 'static/data', file_data), data_folder)
    err = check_data(pjoin(root_dir, data_folder))
    print(err)
    if not err:
        model_dir = add_model(file_data, file_config)
        translator = Translate(file_config, model_dir)
        cmd_list = translator.cmd_list
        cmd = '\n'.join(cmd_list)
        print(cmd)
        subprocess.run(cmd, shell=True)
    valid_from_file(file_data, file_config)

# train_from_file('data_kraken.tar.gz', 'sample_tess_continue.json')



