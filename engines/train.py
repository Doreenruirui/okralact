### Todo: Show all the help info

from parameters import get_parser
from parameters_translator import Translator
from config import Config
import subprocess
from os.path import join as pjoin
import os
import sys
import tarfile


class ENGINE(object):
    def __init__(self, engine_name, paras):
        self.name = engine_name
        self.paras = paras

    def run(self):
        method = getattr(self, self.name, lambda:"Invalid Engine")
        return method()

    def kraken(self):
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix)
        print('loading kraken ...')
        cmd_list = []
        cmd_list.append('source activate kraken')
        cmd_list.append('ketos train ./data/*.png -o %s -N %d' % (model_prefix, self.paras.nepoch))
        # cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)

    def ocropus(self):
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix)
        print(model_prefix)
        # self.paras.nepoch=1
        print('loading ocropus ...')
        nfiles = int(subprocess.check_output('ls data/*.png | wc -l', shell=True).strip())
        print(nfiles)
        cmd_list = []
        cmd_list.append('source activate ocropus_env')
        cmd_list.append('ocropus-rtrain ./data/*.png -o %s -N %d  --savefreq %s' % (model_prefix, self.paras.nepoch * nfiles, self.paras.savefreq))
        # cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)

    def tesseract(self):
        return 'loading tesseract ...'

    def calamari(self):
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix + '_')
        print(model_prefix)
        print('loading ocropus ...')
        nfiles = int(subprocess.check_output('ls data/*.png | wc -l', shell=True).strip())
        print(nfiles)
        cmd_list = []
        cmd_list.append('source activate calamari')
        cmd_list.append('calamari-train --files ./data/*.png --output_model_prefix %s --batch_size 1 --max_iters %d' % (model_prefix, self.paras.nepoch * nfiles))
        # cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)


def clear_data():
    list_files = os.listdir(os.path.join(os.getcwd(), 'data'))
    if len(list_files) != 0:
        subprocess.run('rm -r ./data/*', shell=True)


def train(configs, engine):
    print(configs)
    translator = Translator(configs, engine)
    new_configs = translator.new_configs
    print(new_configs)
    clear_data()
    extract_file(configs.data_file)
    file_prefix = configs.data_file.rsplit('/', 1)[1].rsplit('.', 2)[0]
    err = check_data('./data')
    if not err:
        data_folder = './data'
        config_file = os.path.join(data_folder, 'config.txt')
    cur_folder = os.getcwd()
    configs.model_dir = pjoin(cur_folder, 'model', file_prefix)
    if not os.path.exists(configs.model_dir):
        os.makedirs(configs.model_dir)
    configs.data_dir = data_folder
    configs.nepoch = 1
    train(configs)
    # engine = paras.engine
    # # print('tar -zvcf ../static/data/%s' % filename)
    # # subprocess.run('tar -zvxf ../static/data/%s' % filename, shell=True)
    # print('You have chosen engine %s' % engine)
    # engine = ENGINE(engine, paras)
    # engine.run()
    # clear_data()


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
            if not os.path.exists(os.path.join(data_folder, prefix + '.gt.txt')):
                return 1
            if flag_empty:
                flag_empty = 0
    if flag_empty:
        return 2
    if not os.path.exists(os.path.join(data_folder, 'config.txt')):
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
                _tar.extract(tarinfo, './data')


def train_from_file(filename):
    clear_data()
    extract_file(filename)
    file_prefix = filename.rsplit('/', 1)[1].rsplit('.', 2)[0]
    err = check_data('./data')
    if not err:
        data_folder = './data'
        config_file = os.path.join(data_folder, 'config.txt')
    configs = Config(config_file)
    cur_folder = os.getcwd()
    configs.model_dir = pjoin(cur_folder, 'model', file_prefix)
    if not os.path.exists(configs.model_dir):
        os.makedirs(configs.model_dir)
    configs.data_dir = data_folder
    configs.nepoch = 1
    train(configs)


if __name__ == "__main__":
    # print(sys.argv[1])
    # configs = Config(sys.argv[1])
    # print(configs.model_dir)
    # train(configs)
    # train_from_file(sys.argv[1])
    configs = get_parser()
    engine = sys.argv[1]
    train(configs, engine)



