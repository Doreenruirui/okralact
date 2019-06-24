import tarfile
import os
from os.path import join as pjoin
import subprocess
import random
import numpy as np
from shutil import move


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
                _tar.extract(tarinfo, 'engines/' + foldername)


def clear_data(foldername):
    list_files = os.listdir(pjoin(os.getcwd(), 'engines/' + foldername))
    if len(list_files) != 0:
        subprocess.run('rm -r engines/%s/*' % foldername, shell=True)


def split_train_test(foldername, train_ratio=0.9):
    files = []
    for fn in os.listdir(foldername):
        if fn.endswith('.png'):
            prefix = fn.split('.')[0]
            if os.path.exists(pjoin(foldername, prefix + '.gt.txt')):
                files.append(prefix)
    random.shuffle(files)

    nfile = len(files)
    ntrain = int(np.round(nfile * train_ratio))
    train_files = files[:ntrain]
    eval_files = files[ntrain:]

    train_dir = pjoin(foldername, 'train')
    eval_dir = pjoin(foldername, 'valid')

    if not os.path.exists(train_dir):
        print(train_dir)
        os.makedirs(train_dir)
    if not os.path.exists(eval_dir):
        os.makedirs(eval_dir)

    for fn in train_files:
        move(pjoin(foldername, fn + '.png'), pjoin(train_dir, fn + '.png'))
        move(pjoin(foldername, fn + '.gt.txt'), pjoin(train_dir, fn + '.gt.txt'))
    for fn in eval_files:
        move(pjoin(foldername, fn + '.png'), pjoin(eval_dir, fn + '.png'))
        move(pjoin(foldername, fn + '.gt.txt'), pjoin(eval_dir, fn + '.gt.txt'))

    return train_files, eval_files



