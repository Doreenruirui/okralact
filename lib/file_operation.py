import os
from os.path import join as pjoin
import json
import tarfile
from shutil import rmtree
import uuid


model_root = os.getcwd() + '/static/model'
data_root = os.getcwd() + '/static/data'
config_root = os.getcwd() + '/static/configs'
eval_root = os.getcwd()  + '/static/eval'
train_dir = os.getcwd() + '/engines/data'



def add_model(file_data, file_config):
    model_file = pjoin(model_root, 'model_list')
    model_dict = list_model_dir()
    print(model_dict)
    key = (file_data, file_config)
    if key not in model_dict:
        uni_model_dir = uuid.uuid4().hex
        model_dict[key] = uni_model_dir
        model_dir = pjoin(model_root, uni_model_dir)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        with open(model_file, 'w') as f_:
            for ele in model_dict:
                f_.write('%s\t%s\t%s\n' % (ele[0], ele[1], model_dict[ele]))
        model_name = uni_model_dir
    else:
        model_name = None
    return model_name


def list_model_dir():
    model_file = pjoin(model_root, 'model_list')
    model_dict = {}
    if os.path.exists(model_file):
        with open(model_file) as f_:
            for line in f_:
                items = line.strip().split('\t')
                model_dict[tuple(items[:-1])] = items[-1]
    return model_dict


def del_model_dir(trainset, config):
    model_file = pjoin(model_root, 'model_list')
    model_dir = get_model_dir(trainset, config)
    model_folder = os.path.join(model_root, model_dir)
    if os.path.exists(model_folder):
        rmtree(model_folder, ignore_errors=True)
    if os.path.exists(model_file):
        with open(model_file) as f_:
            out_lines = f_.readlines()
        with open(model_file, 'w') as f_:
            for line in out_lines:
                items = line.strip().split('\t')
                if items[-1] != model_dir:
                    f_.write(line)

def get_model_dir(file_data, file_config):
    model_dict = list_model_dir()
    print(model_dict)
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
    files_list = [ele for ele in os.listdir(data_root) if ele.endswith('.tar.gz')]
    return files_list


def get_configs():
    configs_list = os.listdir(config_root)
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

def update_list(filename, to_del):
    if os.path.exists(filename):
        with open(filename) as f_:
            content = f_.readlines()
        with open(filename, 'w')  as f_:
            for line in content:
                items = line.strip().split('\t')
                if items[-1] != to_del:
                    f_.write(line)
                else:
                    print('file  find', filename)


def write_list(filename, dict_res):
    with open(filename, 'w') as f_:
        for key in dict_res:
            f_.write('\t'.join(key) + '\t' + dict_res[key] + '\n')


def read_json(json_file):
    with open(json_file) as f_:
        content = f_.read()
        return json.loads(content)

def read_config(json_file):
    with open(json_file) as f_:
        content = f_.read()
        try:
            return json.loads(content),  ''
        except ValueError as e:
            return {}, e.args

def read_config_str(json_str):
    try:
        return json.loads(json_str),  ''
    except ValueError as e:
        return {}, e.args

def write_json(dict_res, json_file):
    with open(json_file, 'w') as f_:
        json.dump(dict_res, f_)


def extract_file(filename, foldername):
    with tarfile.open(filename, 'r:gz') as _tar:
        for tarinfo in _tar:
            if tarinfo.isdir():
                continue
            # print('name', tarinfo.name)
            if '/' in tarinfo.name:
                fn = tarinfo.name.split('/', 1)[1]
                if fn.startswith('.'):
                    continue
                tarinfo.name = fn

            _tar.extract(tarinfo, foldername)

def compress_file(files, dest_name):
    print(dest_name)
    print(files)
    with tarfile.open(dest_name, "w:gz") as tar:
        for fn in files:
            path, filename  =  fn.rsplit('/', 1)
            # print(filename)
            tar.add(fn, arcname=filename)
            # tar.add(fn)

def clear_data(foldername):
    if os.path.exists(foldername):
        rmtree(foldername)
    os.makedirs(foldername)

# extract_file('/Users/ruidong/Documents/Experiment/okralact/static/tmp/148c0d837a2d40bab256a94d79cc83d2.tar.gz', '/Users/ruidong/Documents/Experiment/okralact/static/model/7fcb136c02074bd8b3a1edbd4aa6929d')
