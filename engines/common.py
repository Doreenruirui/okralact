import tarfile
import os
from os.path import join as pjoin
import subprocess


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
