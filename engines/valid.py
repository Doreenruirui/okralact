import subprocess
from os.path import join as pjoin
import os
from engines.common import clear_data, read_json
from evaluate.evaluation import evaluate
from shutil import copyfile, move
from collections import OrderedDict
from engines import act_environ, model_root, valid_folder, data_folder
from engines.process_tesseract import convert_image, get_all_files
from lib.file_operation import get_model_dir


def read_report(model_dir):
    dict_res = OrderedDict()
    best_model = -1
    best_perform = -1
    if os.path.exists(pjoin(model_root, model_dir, 'report')):
        with open(pjoin(model_root, model_dir, 'report')) as f_:
            for line in f_:
                print(line)
                if len(line.strip()) > 0:
                    model_name, eval_res = line.strip().split(',', 1)
                    eval_res = eval_res.strip()
                    index = model_name.split(':')[1].strip()
                    dict_res[int(index)] = (eval_res, index)
                    performance = float(eval_res.split(',')[3].split(':')[1].strip())
                    if performance > best_perform:
                        best_model = index
                        best_perform = performance
    # print(dict_res)
    return dict_res, best_perform, best_model


def get_model_postfixes(engine, model_dir, model_prefix):
    dict_postfix = {"kraken": 'mlmodel', 'calamari': 'index',
                    'ocropus': 'pyrnn.gz', 'tesseract': 'checkpoint'}
    if engine == 'tesseract':
        models = [ele.split('.')[0] for ele in os.listdir(pjoin(model_root, model_dir, 'checkpoint'))
                  if ele.endswith(dict_postfix[engine])
                  and 'best' not in ele and ele.startswith('tess_')]
    else:
        models = [ele.split('.')[0] for ele in os.listdir(pjoin(model_root, model_dir))
                  if ele.endswith(dict_postfix[engine])
                  and 'best' not in ele]
    if engine == 'kraken':
        return sorted([ele.split('_')[1] for ele in models])
    elif engine == 'calamari':
        return sorted([ele.split('_')[1] for ele in models])
    elif engine == 'ocropus':
        return sorted([ele.split('-')[1] for ele in models])
    else:
        return sorted([ele.split('_')[1] for ele in models])


def get_model_path(engine, model_prefix, index):
    if engine == 'kraken':
        model_str = '%s_%s.mlmodel'
    elif engine == 'calamari':
        model_str = '%s_%s.ckpt'
    elif engine == 'ocropus':
        model_str = '%s-%s.pyrnn.gz'
    else:
        model_str = 'checkpoint/%s_%s.checkpoint'
    return model_str % (model_prefix, index)


def get_cmd(engine, model_file):
    if engine == 'kraken':
        cmd = 'kraken -I \'%s/*.png\' -o .txt ocr -m %s -s' % (valid_folder, model_file)
    elif engine == 'calamari':
        cmd = 'calamari-predict --checkpoint %s --files %s/*.png' % (model_file, valid_folder)
    elif engine == 'ocropus':
        cmd = 'ocropus-rpred -m %s \'%s/*.png\'' % (model_file, valid_folder)
    return cmd


def rename_calamari_prediction():
    for fn in os.listdir('engines/valid'):
        if fn.endswith('.png'):
            prefix = fn.split('.')[0]
            move('engines/valid/%s.pred.txt' % prefix,
                 'engines/valid/%s.txt' % prefix)


def copy_best_model(engine, model_dir, model_prefix, best_model_index):
    print("Model %s is the best model" % best_model_index)
    abs_model_dir = pjoin(model_root, model_dir)
    if engine == 'kraken':
        best_model_file = '%s_%s.mlmodel' % (model_prefix, best_model_index)
        dest_model_file = 'valid_best.mlmodel'
        copyfile(pjoin(abs_model_dir, best_model_file),
                 pjoin(abs_model_dir, dest_model_file))
    elif engine == 'calamari':
        best_model_file ='%s_%s.ckpt' % (model_prefix, best_model_index)
        dest_model_file = 'valid_best.ckpt'
        for ele in os.listdir(abs_model_dir):
            if ele.startswith(best_model_file):
                postfix = '.' + ele.rsplit('.', 1)[1]
                copyfile(pjoin(abs_model_dir, best_model_file + postfix),
                         pjoin(abs_model_dir, dest_model_file + postfix))
    elif engine == 'ocropus':
        best_model_file = '%s-%s.pyrnn.gz' % (model_prefix, best_model_index)
        dest_model_file = 'valid_best.pyrnn.gz'
        copyfile(pjoin(abs_model_dir, best_model_file),
                 pjoin(abs_model_dir, dest_model_file))
    else:
        best_model_file = '%s_%s.checkpoint' % (model_prefix, best_model_index)
        dest_model_file = 'valid_best.checkpoint'
        copyfile(pjoin(abs_model_dir, 'checkpoint', best_model_file), pjoin(abs_model_dir, 'checkpoint', dest_model_file))


# def eval_from_file(model_dir, engine, model_prefix):
def valid_from_file(file_train, file_config):
    configs = read_json(pjoin('static/configs', file_config))
    model_dir = get_model_dir(file_train, file_config)
    engine = configs["engine"]
    common_schema = read_json("engines/schemas/common.schema")
    model_prefix = configs["model_prefix"] if "model_prefix" in configs \
        else common_schema["definitions"]["model_prefix"]["default"]
    # noinspection PyInterpreter
    dict_res, best_perform, best_model = read_report(model_dir)
    # write the evaluation report
    f_out = open(pjoin(model_root, model_dir, 'report'), 'w')
    model_postfix = get_model_postfixes(engine, model_dir, model_prefix)
    if len(model_postfix) == 0:
        return 'No model yet.'
    for index in model_postfix:
        if int(index) not in dict_res:
            model_file = get_model_path(engine, model_prefix, index)
            model_path = pjoin(model_root, model_dir, model_file)
            if engine == 'tesseract':
                cmd_list = ['export TESSDATA_PREFIX=%s' % pjoin(os.getcwd(), model_root, model_dir),
                            '/Users/doreen/Documents/Experiment/Package/tesseract/src/training/lstmtraining --stop_training --continue_from %s --traineddata %s --model_output %s' %
                            (model_path,
                             pjoin(model_root, model_dir, model_prefix, '%s.traineddata' % model_prefix),
                             pjoin(model_root, model_dir, model_prefix + '.traineddata'))]
                convert_image(valid_folder)
                image_files = get_all_files(data_folder=valid_folder, postfix='.tif')
                for imf in image_files:
                    cmd_list.append(
                        'tesseract -l %s %s/%s.tif %s/%s ' % (model_prefix, valid_folder, imf, valid_folder, imf))
            else:
                cmd_list = [act_environ(engine)]
                cmd_list.append(get_cmd(engine, model_path))
                cmd_list.append('conda deactivate')
            cmd = '\n'.join(cmd_list)
            subprocess.run(cmd, shell=True)
            if engine == 'calamari':
                rename_calamari_prediction()
            gt_files = [valid_folder + '/' + ele for ele in os.listdir(valid_folder) if ele.endswith('.gt.txt')]
            res_str = evaluate(gt_files)
            if float(res_str["char_error_rate"]) > best_perform:
                best_perform = float(res_str["char_error_rate"])
                best_model = index
            f_out.write('Iteration: %s, errors: %d, missing: %d, total: %d, char error rate: %s\n'
                        % (index, res_str["errors"], res_str["missing"], res_str["total"], res_str["char_error_rate"]))
        else:
            res_str = dict_res[int(index)]
            f_out.write('Iteration: %s, %s\n' % (res_str[1], res_str[0]))
    copy_best_model(engine, model_dir, model_prefix, best_model)

valid_from_file('data_kraken.tar.gz', 'sample_calamari.json')
# eval_from_file(model_dir='tess_new', engine='tesseract', model_prefix='tess')