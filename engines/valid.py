from engines.train import clear_data
from engines.validate_parameters import read_json
import subprocess
from subprocess import check_output
from os.path import join as pjoin
import os
from lib.file_operation import get_model_dir
from evaluate.levenshtein import align
from engines.common import clear_data, extract_file
from engines.process_tesseract import convert_image, get_all_files
from evaluate.evaluation import evaluate
from engines import valid_folder, act_environ, deact_environ


def evl_pair():
    gt_files = [ele for ele in os.listdir(valid_folder) if ele.endswith('gt.txt')]
    pred_files = [ele.strip('.gt.txt') + '.txt' for ele in gt_files]
    gt_lines = []
    for fn in gt_files:
        with open('engines/eval/%s' % fn) as f_:
            line = f_.readlines()[0].strip()
            gt_lines.append(line)
    pred_lines = []
    for fn in pred_files:
        if not os.path.exists(pjoin('engines/eval', fn)):
            pred_lines.append('')
            print('not exist:', fn)
            continue
        with open('engines/eval/%s' % fn) as f_:
            lines = f_.readlines()
            if len(lines) > 0:
                line = lines[0].strip()
            else:
                print('empty: ', fn)
                line = ''
            pred_lines.append(line)
    print(gt_lines[0:10],  pred_lines[0:10])
    sum_dis = 0
    sum_len = 0
    for pdl, gtl in zip(pred_lines, gt_lines):
        sum_dis += align(pdl, gtl)
        sum_len += len(gtl)
    print(sum_len)
    print(sum_dis)
    return sum_dis * 1. / sum_len


def eval_from_file(model_dir, engine, model_name):
    clear_data(valid_folder)
    # noinspection PyInterpreter
    if engine == 'kraken':
        cmd = 'kraken -I \'%s/*.png\' -o .txt ocr -m static/model/%s/%s -s' \
              % (valid_folder,  model_dir, model_name)
    elif engine == 'calamari':
        with open('static/model/%s/checkpoint' % model_dir) as f_:
            model_file = f_.readlines()[0].split('"')[1]
        cmd = 'calamari-predict --checkpoint %s --files %s/*.png' % (model_file, valid_folder)
    elif engine == 'ocropus':
        list_model = [ele.split('.')[0].split('-')[1] for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.pyrnn.gz')]
        newest_model = max(list_model)
        prefix = 'ocropus'
        for ele in os.listdir('static/model/%s' % model_dir):
            if ele.endswith('.pyrnn.gz'):
                prefix = ele.split('.')[-3].split('-')[0]
                break
        print(newest_model)
        print(prefix)
        model_file = 'static/model/%s/%s-%s.pyrnn.gz' % (model_dir, prefix, newest_model)
        print(model_file)
        cmd = 'ocropus-rpred -m %s \'engines/eval/*.png\'' % model_file
    else:
        cmd_list = ['export TESSDATA_PREFIX=%s' % pjoin(os.getcwd(), 'static/model', model_dir)]
        convert_image('engines/eval')
        image_files = get_all_files(data_folder='engines/eval', postfix='.tif')
        for imf in image_files:
            cmd_list.append('tesseract -l %s engines/eval/%s.tif engines/eval/%s ' % (model_name, imf, imf))
    cmd = '\n'.join([act_environ(engine), cmd, deact_environ]) if engine != 'tesseract' else '\n'.join(cmd_list)
    subprocess.run(cmd, shell=True)
    gt_files = ['engines/eval/' + ele for ele in os.listdir('engines/eval') if ele.endswith('.gt.txt')]
    res_str = str(evaluate(gt_files))
    return res_str





