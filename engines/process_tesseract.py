import subprocess
from shutil import copyfile, rmtree
import os
from os.path import join as pjoin
from PIL import Image
import io
import unicodedata
import random
from engines import valid_folder


def get_all_files(data_folder, postfix='.png'):
    return [ele.rsplit('.', 1)[0] for ele in os.listdir(data_folder) if ele.endswith(postfix)]


def convert_image(data_folder):
    # convert image to tif
    for fn in get_all_files(data_folder):
        im = Image.open(pjoin(data_folder, fn + '.png'))
        im.save(pjoin(data_folder, fn + '.tif'))
        # os.remove(pjoin(data_folder, fn + '.png'))

def get_box_str(data_folder,  fn):
    with open(pjoin(data_folder, fn + '.tif'), "rb") as f:
        width, height = Image.open(f).size
    # load gt
    with io.open(pjoin(data_folder, fn + '.gt.txt'), "r", encoding='utf-8') as f:
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
    return box_str

def generate_box(data_folder, tmp_folder):
    # load image
    with open(pjoin(tmp_folder, 'all-boxes'), 'w') as f_all:
        for fn in get_all_files(data_folder, '.tif'):
            box_str = get_box_str(data_folder,  fn)
            with open(pjoin(data_folder, fn + '.box'), 'w') as f_:
                f_.write(box_str)
            f_all.write(box_str)
        for fn in get_all_files(valid_folder, '.tif'):
            box_str = get_box_str(valid_folder,  fn)
            with open(pjoin(valid_folder, fn + '.box'), 'w') as f_:
                f_.write(box_str)
            f_all.write(box_str)


def generate_unicharset(tmp_folder):
    subprocess.run('/Users/doreen/Documents/Experiment/Package/tesseract/src/training/unicharset_extractor --output_unicharset "%s" --norm_mode 1 "%s"'
                   % (pjoin(tmp_folder, "unicharset"), pjoin(tmp_folder, "all-boxes")),
                   shell=True)


def generate_lstmf(data_folder, tmp_folder):
    for fn in get_all_files(data_folder, '.tif'):
        subprocess.run('tesseract %s.tif %s --psm 7 lstm.train' %
                       (pjoin(data_folder, fn), pjoin(data_folder, fn)), shell=True)
    for fn in get_all_files(valid_folder, '.tif'):
        subprocess.run('tesseract %s.tif %s --psm 7 lstm.train' %
                       (pjoin(valid_folder, fn), pjoin(valid_folder, fn)), shell=True)
    with open(pjoin(tmp_folder, 'all-lstmf'), 'w') as f_:
        lstmf_files = get_all_files(data_folder, '.lstmf')
        random.shuffle(lstmf_files)
        for fn in lstmf_files:
            f_.write(pjoin(data_folder, fn + '.lstmf'))
            f_.write('\n')


def generate_protomodel(tmp_folder, model_folder, model_prefix):
    copyfile('static/docs/radical-stroke.txt', pjoin(tmp_folder, 'radical-stroke.txt'))
    copyfile('static/docs/Latin.unicharset', pjoin(tmp_folder, 'Latin.unicharset'))
    if not os.path.exists(model_folder):
        os.makedirs(model_folder)
    cmd = '/Users/doreen/Documents/Experiment/Package/tesseract/src/training/combine_lang_model --input_unicharset %s --script_dir %s --output_dir %s --lang %s' %\
          (pjoin(tmp_folder, 'unicharset'), tmp_folder, model_folder, model_prefix)
    print(cmd)
    subprocess.run(cmd, shell=True)


def get_numofchar(tmp_folder):
    with open(pjoin(tmp_folder, 'unicharset')) as f_:
        nchar = int(f_.readlines()[0].strip())
    return nchar


def preprocess(data_folder, tmp_folder, model_folder, checkpoint_folder, model_prefix):
    if os.path.exists(model_folder):
        rmtree(model_folder)
    os.makedirs(model_folder)
    if os.path.exists(checkpoint_folder):
        rmtree(checkpoint_folder)
    os.makedirs(checkpoint_folder)
    convert_image(data_folder)
    convert_image(valid_folder)
    generate_box(data_folder, tmp_folder)
    generate_unicharset(tmp_folder)
    generate_lstmf(data_folder, tmp_folder)
    generate_protomodel(tmp_folder, model_folder, model_prefix)


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




