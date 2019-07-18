import tarfile
import os
from os.path import join as pjoin
import subprocess
import random
import numpy as np
from shutil import rmtree
import json


def read_json(json_file):
    with open(json_file) as f_:
        data = json.loads(f_.read())
    return data


def write_json(dict_res, json_file):
    with open(json_file, 'w') as f_:
        json.dump(dict_res, f_)


def extract_file(filename, foldername):
    with tarfile.open(filename, 'r:gz') as _tar:
        for tarinfo in _tar:
            if tarinfo.isdir():
                continue
            fn = tarinfo.name.split('/')[1]
            if fn.startswith('.'):
                continue
            if fn.endswith('.png') or tarinfo.name.endswith('.txt'):
                tarinfo.name = fn
                _tar.extract(tarinfo, foldername)


def clear_data(foldername):
    if os.path.exists(foldername):
        rmtree(foldername)
    os.makedirs(foldername)


def split_train_test(data_folder, tmp_folder, train_ratio=0.9, engine='kraken'):
    files = []
    for fn in os.listdir(data_folder):
        if fn.endswith('.png'):
            prefix = fn.split('.')[0]
            if os.path.exists(pjoin(data_folder, prefix + '.gt.txt')):
                files.append(prefix)
    random.shuffle(files)

    nfile = len(files)
    ntrain = int(np.floor(nfile * train_ratio))
    ntest = nfile - ntrain
    train_files = files[:ntrain]
    eval_files = files[ntrain:]
    if ntest == 0 and engine == 'kraken':
        ntest = int(np.ceil(nfile * 0.1))
        eval_files = files[:nfile][-ntest:]

    if engine == 'tesseract':
        postfix = '.lstmf'
    else:
        postfix = '.png'

    if len(train_files) > 0:
        with open(pjoin(tmp_folder, 'list.train'), 'w') as f_:
            for fn in train_files:
                f_.write(pjoin(data_folder, fn + postfix) + '\n')
    if len(eval_files) > 0:
        with open(pjoin(tmp_folder, 'list.eval'), 'w') as f_:
            for fn in eval_files:
                f_.write(pjoin(data_folder, fn + postfix) + '\n')
    return ntrain, ntest
