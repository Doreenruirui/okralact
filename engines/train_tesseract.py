import subprocess
import os
from os.path import join as pjoin
from PIL import Image
import io
import unicodedata
import random
import numpy as np


data_folder = 'engines/data'
tmp_folder = 'engines/tmp'
model_folder = 'engines/tmp/model'
checkpoint_folder = 'engines/tmp/model/checkpoints'


def get_all_files(postfix='.png'):
    return [ele.rsplit('.', 1)[0] for ele in os.listdir(data_folder) if ele.endswith(postfix)]


def covert_image():
    # convert image to tif
    for fn in get_all_files():
        im = Image.open(pjoin(data_folder, fn + '.png'))
        im.save(pjoin(data_folder, fn + '.tif'))
        os.remove(pjoin(data_folder, fn + '.png'))


def generate_box():
    # load image

    with open(pjoin(tmp_folder, 'all-boxes'), 'w') as f_all:
        for fn in get_all_files('.tif'):
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
            with open(pjoin(data_folder, fn + '.box'), 'w') as f_:
                f_.write(box_str)
            f_all.write(box_str)


def generate_unicharset():
    subprocess.run('unicharset_extractor --output_unicharset "%s" --norm_mode 1 "%s"'
                   % (pjoin(tmp_folder, "unicharset"), pjoin(tmp_folder, "all-boxes")),
                   shell=True)


def generate_lstmf():
    for fn in get_all_files('.tif'):
        subprocess.run('tesseract %s.tif %s --psm 7 lstm.train' %
                       (pjoin(data_folder, fn), pjoin(data_folder, fn)), shell=True)
    with open(pjoin(tmp_folder, 'all-lstmf'), 'w') as f_:
        lstmf_files = get_all_files('.lstmf')
        random.shuffle(lstmf_files)
        for fn in lstmf_files:
            f_.write(pjoin(data_folder, fn + '.lstmf'))
            f_.write('\n')


def split_train_test(train_ratio=0.9):
    with open(pjoin(tmp_folder, 'all-lstmf')) as f_:
        lines = f_.readlines()
    nline = len(lines)
    ntrain = int(np.round(nline * train_ratio))
    with open(pjoin(tmp_folder, 'list.train'), 'w') as f_:
        for i in range(ntrain):
            f_.write(lines[i])
    with open(pjoin(tmp_folder, 'list.eval'), 'w') as f_:
        for i in range(ntrain, nline):
            f_.write(lines[i])


def generate_protomodel():
    subprocess.run('wget -O %s https://github.com/tesseract-ocr/langdata_lstm/raw/master/radical-stroke.txt'
                   % (pjoin(tmp_folder, 'radical-stroke.txt')), shell=True)
    subprocess.run('wget -O %s https://github.com/tesseract-ocr/langdata/raw/master/Latin.unicharset'
                   % (pjoin(tmp_folder, 'Latin.unicharset')), shell=True)
    subprocess.run('mkdir %s' % model_folder, shell=True)
    subprocess.run('combine_lang_model --input_unicharset %s --script_dir %s --output_dir %s --lang model'
                   % (pjoin(tmp_folder, 'unicharset'), tmp_folder, tmp_folder), shell=True)


def train_model(model_name='model'):
    if not os.path.exists(checkpoint_folder):
        os.makedirs(checkpoint_folder)
    with open(pjoin(tmp_folder, 'unicharset')) as f_:
        nchar = f_.readlines()[0].strip()
    cmd = 'lstmtraining ' \
          '--traineddata %s ' \
          '--net_spec "[1,36,0,1 Ct3,3,16 Mp3,3 Lfys48 Lfx96 Lrx96 Lfx256 O1c%s]" ' \
          '--model_output %s ' \
          '--learning_rate 20e-4 ' \
          '--train_listfile %s ' \
          '--eval_listfile %s ' \
          '--max_iterations 10000' % (pjoin(model_folder, 'model.traineddata'),
                                      nchar,
                                      pjoin(checkpoint_folder, model_name),
                                      pjoin(tmp_folder, 'list.train'),
                                      pjoin(tmp_folder, 'list.eval'))
    print(cmd)
    subprocess.run(cmd, shell=True)


def main():
    if not os.path.exists(tmp_folder):
        os.makedirs(tmp_folder)
    covert_image()
    generate_box()
    generate_unicharset()
    generate_lstmf()
    split_train_test()
    generate_protomodel()
    train_model()


main()



