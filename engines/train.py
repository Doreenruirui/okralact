### Todo: Show all the help info

# from parameters import get_parser
from engines.validate_parameters import read_json
from engines.parameters_translator import Translate
import subprocess
from subprocess  import check_output
from os.path import join as pjoin
import os
import uuid
import tarfile
import shutil
from lib.file_operation import list_model_dir, get_model_dir
from evaluate.levenshtein import align


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


def evl_pair():
    gt_files = [ele for ele in os.listdir('engine/data/') if ele.endswith('gt.txt')]
    pred_files = [ele for ele in os.listdir('engine/data/') if ele.endswith('.txt') and '.gt.' not in ele]
    gt_lines = []
    for fn in gt_files:
        with open('engine/data/%s' % fn) as f_:
            line = f_.readlines()[0]
            gt_lines.append(line)
    pred_lines = []
    for fn in pred_files:
        with open('engine/data/%s' % fn) as f_:
            line = f_.readlines()[0]
            pred_lines.append(line)
    sum_dis = 0
    sum_len = 0
    for pdl, gtl in zip(pred_lines, gt_lines):
        sum_dis += align(pdl, gtl)
        sum_len = len(gtl)
    return sum_dis * 1. / sum_len


def eval_from_file(file_test, file_train, file_config):
    clear_data()
    root_dir = os.getcwd()
    print(root_dir)
    extract_file(pjoin(root_dir, 'static/data', file_test))
    configs = read_json(pjoin(root_dir, 'static/configs', file_config))
    print(configs)
    model_dir = get_model_dir(file_train, file_config)
    # noinspection PyInterpreter
    if configs["engine"] == 'kraken':
        cmd_list = ['source activate kraken']
        cmd_list.append('ketos test -m static/model/%s/kraken_best.mlmodel engines/data/*.png' % model_dir)
        cmd_list.append('conda deactivate')
        cmd = '\n'.join(cmd_list)
        print(cmd)
        res_str = check_output(cmd, shell=True)
        res_str = res_str.split(b'\n')[-2]
        print(res_str)
        return res_str
    elif configs["engine"] == 'calamari':
        cmd_list = ['source activate calamari']
        ckpt_file = 'static/model/%s/checkpoint' % model_dir
        with open(ckpt_file) as f_:
            model_file = f_.readlines()[0].split('"')[1]
        cmd_list.append('calamari-predict --checkpoint %s --files engines/data/*.png' % model_file)
        cmd_list.append('conda deactivate')
        cmd = '\n'.join(cmd_list)
        print(cmd)
        subprocess.run(cmd, shell=True)
        res_str = str(evl_pair())
        return res_str
    elif configs["engine"] == 'ocropus':
        cmd_list = ['source activate ocropus']
        list_model = [ele.split('.')[0].split('-')[1] for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.pyrnn.gz')]
        newest_model = max(list_model)
        for ele in os.listdir('static/model/%s' % model_dir):
            if ele.endswith('.pyrnn.gz'):
                prefix = ele.split('.')[-3].split('-')
        model_file = 'static/model/%s-%s.pyrnn.gz' % (newest_model, prefix)
        cmd_list.append('calamari-predict --checkpoint %s --files engines/data/*.png' % model_file)
        cmd_list.append('conda deactivate')
        cmd = '\n'.join(cmd_list)
        print(cmd)
        subprocess.run(cmd, shell=True)
        res_str = str(evl_pair())
        return res_str







# train_from_file((sys.argv[1], sys.argv[2]))

