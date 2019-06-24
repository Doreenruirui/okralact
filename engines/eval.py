from engines.train import clear_data
from engines.validate_parameters import read_json
import subprocess
from subprocess import check_output
from os.path import join as pjoin
import os
from lib.file_operation import get_model_dir
from evaluate.levenshtein import align
from engines.common import clear_data, extract_file
from engines.train_tesseract import convert_image, get_all_files
from evaluate.evaluation import evaluate


def evl_pair():
    gt_files = [ele for ele in os.listdir('engines/eval/') if ele.endswith('gt.txt')]
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


def eval_from_file(file_test, file_train, file_config):
    clear_data('eval')
    root_dir = os.getcwd()
    print(root_dir)
    extract_file(pjoin(root_dir, 'static/data', file_test), 'eval')
    configs = read_json(pjoin(root_dir, 'static/configs', file_config))
    print(configs)
    model_dir = get_model_dir(file_train, file_config)
    # noinspection PyInterpreter
    if configs["engine"] == 'kraken':
        cmd_list = ['source activate kraken',
                    'kraken -I \'%s\' -o .txt ocr -m static/model/%s/kraken_best.mlmodel -s'
                    % ('engines/eval/*.png',  model_dir),
                    'conda deactivate']
    elif configs["engine"] == 'calamari':
        with open('static/model/%s/checkpoint' % model_dir) as f_:
            model_file = f_.readlines()[0].split('"')[1]
        cmd_list = ['source activate calamari',
                    'calamari-predict --checkpoint %s --files engines/eval/*.png' % model_file,
                    'conda deactivate']
    elif configs["engine"] == 'ocropus':
        cmd_list = ['source activate ocropus_env']
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
        cmd_list.append('ocropus-rpred -m %s \'engines/eval/*.png\'' % model_file)
        cmd_list.append('conda deactivate')
    elif configs["engine"] == 'tesseract':
        if "prefix" in configs:
            model_name = configs["prefix"]
        else:
            model_name = configs["engine"]
        cmd_list = ['export TESSDATA_PREFIX=%s' % pjoin(os.getcwd(), 'static/model', model_dir)]
        convert_image('engines/eval')
        image_files = get_all_files(data_folder='engines/eval', postfix='.tif')
        for imf in image_files:
            cmd_list.append('tesseract -l %s engines/eval/%s.tif engines/eval/%s ' % (model_name, imf, imf))
    cmd = '\n'.join(cmd_list)
    subprocess.run(cmd, shell=True)
    gt_files = ['engines/eval/' + ele for ele in os.listdir('engines/eval') if ele.endswith('.gt.txt')]
    res_str = str(evaluate(gt_files))
    return res_str





