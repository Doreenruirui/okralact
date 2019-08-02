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
from engines import eval_folder, model_root, data_root, config_root, act_environ, deact_environ
from engines import act_environ, model_root, valid_folder, data_folder


def evl_pair():
    gt_files = [ele for ele in os.listdir(eval_folder) if ele.endswith('gt.txt')]
    pred_files = [ele.strip('.gt.txt') + '.txt' for ele in gt_files]
    gt_lines = []
    for fn in gt_files:
        with open('%s/%s' % (eval_folder, fn)) as f_:
            line = f_.readlines()[0].strip()
            gt_lines.append(line)
    pred_lines = []
    for fn in pred_files:
        if not os.path.exists(pjoin(eval_folder, fn)):
            pred_lines.append('')
            print('not exist:', fn)
            continue
        with open('%s/%s' % (eval_folder, fn)) as f_:
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


def get_best_model_path(engine, model_dir):
    if engine == 'kraken':
        return pjoin(model_root, model_dir, 'best.mlmodel')
    elif engine == 'calamari':
        return pjoin(model_root, model_dir, 'best.ckpt')
    elif engine == 'ocropus':
        return pjoin(model_root, model_dir, 'best.pyrnn.gz')
    else:
        return pjoin(model_root, model_dir, 'checkpoint', 'best.checkpoint')




def eval_from_file(file_test, file_train, file_config):
    clear_data(eval_folder)
    extract_file(pjoin('static/data', file_test), eval_folder)
    configs = read_json(pjoin('static/configs', file_config))
    print(configs)
    model_dir = get_model_dir(file_train, file_config)
    engine = configs["engine"]
    common_schema = read_json("engines/schemas/common.schema")
    model_prefix = configs["model_prefix"] if "model_prefix" in configs \
        else common_schema["definitions"]["model_prefix"]["default"]
    if engine != "tesseract":
        cmd_list = [act_environ(engine)]
    else:
        cmd_list = []
    # noinspection PyInterpreter
    best_model = get_best_model_path(engine, model_dir)
    if engine == 'kraken':
        cmd_list.append('kraken -I \'%s/*.png\' -o .txt ocr -m %s -s'
                        % (eval_folder,  best_model))
    elif engine == 'calamari':
        cmd_list.append('calamari-predict --checkpoint %s --files %s/*.png'
                        % (best_model, eval_folder))
    elif engine == 'ocropus':
        cmd_list.append('ocropus-rpred -m %s \'%s/*.png\'' % (best_model, eval_folder))
    elif engine == 'tesseract':
        cmd_list.append('export TESSDATA_PREFIX=%s' % pjoin(os.getcwd(), model_root, model_dir),
                        'lstmtraining --stop_training --continue_from %s --traineddata %s --model_output %s' %
                        (best_model,
                         pjoin(model_root, model_dir, model_prefix, '%s.traineddata' % model_prefix),
                         pjoin(model_root, model_dir, model_prefix + '.traineddata')))
        cmd_list = ['export TESSDATA_PREFIX=%s' % pjoin(model_root, model_dir)]
        convert_image('engines/eval')
        image_files = get_all_files(data_folder=eval_folder, postfix='.tif')
        for imf in image_files:
            cmd_list.append('tesseract -l %s %s/%s.tif %s/%s ' % (model_prefix,
                                                                  eval_folder,
                                                                  imf,
                                                                  eval_folder,
                                                                  imf))
    cmd = '\n'.join(cmd_list)
    subprocess.run(cmd, shell=True)
    gt_files = [eval_folder + '/' + ele for ele in os.listdir(eval_folder) if ele.endswith('.gt.txt')]
    res_str = str(evaluate(gt_files))
    return res_str





