from engines.train import clear_data
from engines.validate_parameters import read_json
import subprocess
from subprocess  import check_output
from os.path import join as pjoin
import os
from lib.file_operation import get_model_dir
from evaluate.levenshtein import align
from engines.common import clear_data, extract_file


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
        cmd_list = ['source activate kraken']
        image_files = [ele for ele in os.listdir('engines/eval/') if ele.endswith('.png')]
        out_files = [ele.strip('.png') + '.txt' for ele in image_files]
        pairs = ''
        for imf, outf in zip(image_files, out_files):
            pairs +=  '-i engines/eval/%s engines/eval/%s ' % (imf, outf)
        cmd_list.append('kraken %s ocr -m static/model/%s/kraken_best.mlmodel -s' % (pairs,  model_dir))
        cmd_list.append('conda deactivate')
        cmd = '\n'.join(cmd_list)
        print(cmd)
    elif configs["engine"] == 'calamari':
        cmd_list = ['source activate calamari']
        ckpt_file = 'static/model/%s/checkpoint' % model_dir
        with open(ckpt_file) as f_:
            model_file = f_.readlines()[0].split('"')[1]
        cmd_list.append('calamari-predict --checkpoint %s --files engines/eval/*.png' % model_file)
        cmd_list.append('conda deactivate')
        cmd = '\n'.join(cmd_list)
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
        cmd = '\n'.join(cmd_list)

    print(cmd)
    subprocess.run(cmd, shell=True)
    res_str = str(evl_pair())
    return res_str





