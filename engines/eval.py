from engines.validate_parameters import read_json
import subprocess
from os.path import join as pjoin
import os
import uuid
import json
from lib.file_operation import get_model_dir
from engines.common import clear_data, extract_file
from lib.file_operation import read_list, write_list
from engines.process_tesseract import convert_image, get_all_files
from evaluate.evaluation import evaluate
from engines import eval_folder, model_root, data_root, config_root, eval_root, act_environ, deact_environ


def add_eval_report(file_test, file_train, file_config, file_model):
    eval_file = pjoin(eval_root, 'eval_list')
    dict_eval = read_list(eval_file)
    key = (file_test, file_train, file_config, file_model)
    uni_model_dir = uuid.uuid4().hex
    if key in dict_eval:
        old_eval_file = dict_eval[key]
        os.remove(pjoin(eval_root, old_eval_file))
    dict_eval[key] = uni_model_dir
    write_list(eval_file, dict_eval)
    return dict_eval[key]


def get_best_model_path(engine, model_dir):
    if engine == 'kraken':
        return pjoin(model_root, model_dir, 'valid_best.mlmodel')
    elif engine == 'calamari':
        return pjoin(model_root, model_dir, 'valid_best.ckpt')
    elif engine == 'ocropus':
        return pjoin(model_root, model_dir, 'valid_best.pyrnn.gz')
    else:
        return pjoin(model_root, model_dir, 'checkpoint', 'valid_best.checkpoint')


def eval_from_file(file_test, file_train, file_config,  model_file):
    clear_data(eval_folder)
    extract_file(pjoin(data_root, file_test), eval_folder)
    configs = read_json(pjoin(config_root, file_config))
    model_dir = get_model_dir(file_train, file_config)
    engine = configs["engine"]
    common_schema = read_json("engines/schemas/common.schema")
    model_prefix = configs["model_prefix"] if "model_prefix" in configs \
        else common_schema["definitions"]["model_prefix"]["default"]
    cmd_list = [act_environ(engine)] if engine != 'tesseract' else []
    best_model = pjoin(model_root, model_dir, model_file)
    if engine == 'kraken':
        cmd_list.append('kraken -I \'%s/*.png\' -o .txt ocr -m %s -s'
                        % (eval_folder,  best_model))
    elif engine == 'calamari':
        cmd_list.append('calamari-predict --checkpoint %s --files %s/*.png'
                        % (best_model, eval_folder))
    elif engine == 'ocropus':
        cmd_list.append('ocropus-rpred -m %s \'%s/*.png\'' % (best_model, eval_folder))
    elif engine == 'tesseract':
        cmd_list.append('export TESSDATA_PREFIX=%s' % pjoin(model_root, model_dir))
        cmd_list.append('/Users/doreen/Documents/Experiment/Package/tesseract/src/training/lstmtraining --stop_training --continue_from %s --traineddata %s --model_output %s' %
                        (best_model,
                         pjoin(model_root, model_dir, model_prefix, '%s.traineddata' % model_prefix),
                         pjoin(model_root, model_dir, model_prefix + '.traineddata')))
        convert_image('engines/eval')
        image_files = get_all_files(data_folder=eval_folder, postfix='.tif')
        for imf in image_files:
            cmd_list.append('tesseract -l %s %s/%s.tif %s/%s ' % (model_prefix,
                                                                  eval_folder,
                                                                  imf,
                                                                  eval_folder,
                                                                  imf))
    if engine != 'tesseract':
        cmd_list.append(deact_environ)
    cmd = '\n'.join(cmd_list)
    subprocess.run(cmd, shell=True)
    gt_files = [eval_folder + '/' + ele for ele in os.listdir(eval_folder) if ele.endswith('.gt.txt')]
    res = evaluate(gt_files)
    res_file = add_eval_report(file_test, file_train, file_config, model_file)
    print(res_file)
    with open(pjoin(eval_root, res_file), 'w') as f_:
        json.dump(res, f_)
    return res_file





