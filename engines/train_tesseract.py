import subprocess
from shutil import copyfile, rmtree
import os
from os.path import join as pjoin
from PIL import Image
import io
import unicodedata
import random
import numpy as np


def get_all_files(data_folder, postfix='.png'):
    return [ele.rsplit('.', 1)[0] for ele in os.listdir(data_folder) if ele.endswith(postfix)]


def convert_image(data_folder):
    # convert image to tif
    for fn in get_all_files(data_folder):
        im = Image.open(pjoin(data_folder, fn + '.png'))
        im.save(pjoin(data_folder, fn + '.tif'))
        os.remove(pjoin(data_folder, fn + '.png'))


def generate_box(folders):
    # load image
    with open(pjoin(folders.tmp_folder, 'all-boxes'), 'w') as f_all:
        for fn in get_all_files(folders.data_folder, '.tif'):
            with open(pjoin(folders.data_folder, fn + '.tif'), "rb") as f:
                width, height = Image.open(f).size

            # load gt
            with io.open(pjoin(folders.data_folder, fn + '.gt.txt'), "r", encoding='utf-8') as f:
                lines = f.read().strip().split('\n')

            box_str = ''
            for line in lines:
                if line.strip():
                    for i in range(1, len(line)):
                        char = line[i]
                        prev_char = line[i - 1]
                        if unicodedata.combining(char):
                            box_str += u"%s %d %d %d %d 0\n" % ((prev_char + char).encode('utf-8'), 0, 0, width, height)
                        elif not unicodedata.combining(prev_char):
                            box_str += u"%s %d %d %d %d 0\n" % (prev_char.encode('utf-8'), 0, 0, width, height)
                    if not unicodedata.combining(line[-1]):
                        box_str += u"%s %d %d %d %d 0\n" % (line[-1].encode('utf-8'), 0, 0, width, height)
                    box_str += "%s %d %d %d %d 0\n" % ("\t", width, height, width + 1, height + 1)
            with open(pjoin(folders.data_folder, fn + '.box'), 'w') as f_:
                f_.write(box_str)
            f_all.write(box_str)


def generate_unicharset(folders):
    subprocess.run('unicharset_extractor --output_unicharset "%s" --norm_mode 1 "%s"'
                   % (pjoin(folders.tmp_folder, "unicharset"), pjoin(folders.tmp_folder, "all-boxes")),
                   shell=True)


def generate_lstmf(folders):
    for fn in get_all_files(folders.data_folder, '.tif'):
        subprocess.run('tesseract %s.tif %s --psm 7 lstm.train' %
                       (pjoin(folders.data_folder, fn), pjoin(folders.data_folder, fn)), shell=True)
    with open(pjoin(folders.tmp_folder, 'all-lstmf'), 'w') as f_:
        lstmf_files = get_all_files(folders.data_folder, '.lstmf')
        random.shuffle(lstmf_files)
        for fn in lstmf_files:
            f_.write(pjoin(folders.data_folder, fn + '.lstmf'))
            f_.write('\n')


def split_train_test(folders, train_ratio=0.9):
    with open(pjoin(folders.tmp_folder, 'all-lstmf')) as f_:
        lines = f_.readlines()
    nline = len(lines)
    ntrain = int(np.round(nline * train_ratio))
    with open(pjoin(folders.tmp_folder, 'list.train'), 'w') as f_:
        for i in range(ntrain):
            f_.write(lines[i])
    with open(pjoin(folders.tmp_folder, 'list.eval'), 'w') as f_:
        for i in range(ntrain, nline):
            f_.write(lines[i])


def generate_protomodel(folders, model_prefix):
    copyfile('static/docs/radical-stroke.txt', pjoin(folders.tmp_folder, 'radical-stroke.txt'))
    copyfile('static/docs/Latin.unicharset', pjoin(folders.tmp_folder, 'Latin.unicharset'))
    if not os.path.exists(folders.model_folder):
        os.makedirs(folders.model_folder)
    cmd = 'combine_lang_model --input_unicharset %s --script_dir %s --output_dir %s --lang %s' %\
          (pjoin(folders.tmp_folder, 'unicharset'), folders.tmp_folder, folders.model_folder, model_prefix)
    print(cmd)
    subprocess.run(cmd, shell=True)


def get_numofchar(folders):
    with open(pjoin(folders.tmp_folder, 'unicharset')) as f_:
        nchar = f_.readlines()[0].strip()
    return nchar


def preprocess(folders, model_prefix):
    if os.path.exists(folders.tmp_folder):
        rmtree(folders.tmp_folder)
    os.makedirs(folders.tmp_folder)
    if os.path.exists(folders.model_folder):
        rmtree(folders.model_folder)
    os.makedirs(folders.model_folder)
    if os.path.exists(folders.checkpoint_folder):
        rmtree(folders.checkpoint_folder)
    os.makedirs(folders.checkpoint_folder)
    convert_image(folders.data_folder)
    generate_box(folders)
    generate_unicharset(folders)
    generate_lstmf(folders)
    generate_protomodel(folders, model_prefix)


# def train():
#     if not os.path.exists(tmp_folder):
#         os.makedirs(tmp_folder)
#     # covert_image()
#     # generate_box()
#     # generate_unicharset()
#     generate_lstmf()
#     split_train_test()
#     generate_protomodel()
#     train_model()
#
# train()




