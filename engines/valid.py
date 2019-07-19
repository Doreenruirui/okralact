import subprocess
from os.path import join as pjoin
import os
from engines.common import clear_data
from engines.process_tesseract import convert_image, get_all_files
from evaluate.evaluation import evaluate
from engines import valid_folder
from shutil import copyfile, move
from collections import OrderedDict


def creat_valid():
    clear_data(valid_folder)
    file_valid = pjoin('engines', 'tmp', 'list.eval')
    with open(file_valid) as f_:
        for line in f_:
            src_file = line.strip()
            dst_file = pjoin('engines/valid', src_file.split('/')[2])
            copyfile(src_file, dst_file)
            copyfile(src_file.rsplit('.', 1)[0] + '.gt.txt', dst_file.rsplit('.', 1)[0] + '.gt.txt')


def read_report(model_dir):
    dict_res = OrderedDict()
    best_model = -1
    best_perform = -1
    if os.path.exists(pjoin('static/model', model_dir, 'report')):
        with open(pjoin('static/model', model_dir, 'report')) as f_:
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


def eval_from_file(model_dir, engine, model_prefix):
    creat_valid()
    # noinspection PyInterpreter
    dict_res, best_perform, best_model = read_report(model_dir)
    # write the evaluation report
    f_out = open(pjoin('static/model', model_dir, 'report'), 'w')



    if engine == 'kraken':
        models = [ele for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.mlmodel') and 'best' not in ele]
        if len(models) == 0:
            return 'No model yet.'
        model_postfixes = sorted([int(ele.split('.')[0].split('_')[1]) for ele in models])
        for index in model_postfixes:
            if index not in dict_res:
                model = model_prefix + '_' + str(index) + '.mlmodel'
                cmd_list = ['source activate kraken',
                            'kraken -I \'%s/*.png\' -o .txt ocr -m static/model/%s/%s -s'
                            % (valid_folder, model_dir, model),
                            'conda deactivate']
                cmd = '\n'.join(cmd_list)
                subprocess.run(cmd, shell=True)
                gt_files = [valid_folder + '/' + ele for ele in os.listdir(valid_folder) if ele.endswith('.gt.txt')]
                res_str = evaluate(gt_files)
                print(model, res_str)
                if float(res_str["char_error_rate"]) > best_perform:
                    best_perform = float(res_str["char_error_rate"])
                    best_model = index
                f_out.write('Iteration: %d, errors: %d, missing: %d, total: %d, char error rate: %s\n'
                            % (index, res_str["errors"],  res_str["missing"], res_str["total"], res_str["char_error_rate"]))
            else:
                res_str = dict_res[index][0]
                f_out.write('Iteration: %d, %s\n' % (index, res_str))
        best_model_file = 'static/model/%s/%s_%d.mlmodel' % (model_dir, model_prefix, str(best_model))
        dest_model_file = 'static/model/%s/best.mlmodel' % model_dir
        print("Model %d is the best model" % best_model)
        copyfile(best_model_file, dest_model_file)
    elif engine == 'calamari':
        models = [ele for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.index')  and 'best' not in ele]
        if len(models) == 0:
            return 'No model yet.'
        model_postfixes = sorted([ele.split('.')[0][len(model_prefix):] for ele in models])
        for index in model_postfixes:
            if int(index) not in dict_res:
                model = model_prefix + index + '.ckpt'
                cmd_list = ['source activate calamari',
                            'calamari-predict --checkpoint static/model/%s/%s --files %s/*.png' % (model_dir, model, valid_folder),
                            'conda deactivate']
                cmd = '\n'.join(cmd_list)
                subprocess.run(cmd, shell=True)
                for fn in os.listdir('engines/valid'):
                    if fn.endswith('.png'):
                        prefix = fn.split('.')[0]
                        move('engines/valid/%s.pred.txt' % prefix,
                             'engines/valid/%s.txt' % prefix)
                gt_files = [valid_folder + '/' + ele for ele in os.listdir(valid_folder) if ele.endswith('.gt.txt')]
                res_str = evaluate(gt_files)
                print(model, res_str)
                if float(res_str["char_error_rate"]) > best_perform:
                    best_perform = float(res_str["char_error_rate"])
                    best_model = index
                f_out.write('Iteration: %s, errors: %d, missing: %d, total: %d, char error rate: %s\n'
                            % (index, res_str["errors"], res_str["missing"], res_str["total"], res_str["char_error_rate"]))
            else:
                res_str = dict_res[int(index)]
                f_out.write('Iteration: %s, %s\n' % (res_str[1], res_str[0]))
            best_model_file = 'static/model/%s/%s%s.ckpt' % (model_dir, model_prefix, best_model)
            dest_model_file = 'static/model/%s/best.ckpt' % model_dir
            print("Model %s is the best model" % best_model)
            for ele in os.listdir('static/model/%s' % model_dir):
                if ele.startswith('%s%s.ckpt' % (model_prefix, best_model)):
                    postfix = '.' + ele.rsplit('.', 1)[1]
                    copyfile(best_model_file + postfix, dest_model_file + postfix)
    elif engine == 'ocropus':
        models = [ele.split('.')[0] for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.pyrnn.gz') and 'best' not in ele]
        if len(models) == 0:
            return 'No model yet.'
        model_postfixes = sorted([ele.split('-')[1] for ele in models])
        for index in model_postfixes:
            if int(index) not in dict_res:
                model = 'static/model/%s/%s-%s.pyrnn.gz' % (model_dir, model_prefix, index)
                cmd_list = ['source activate ocropus_env',
                            'ocropus-rpred -m %s \'%s/*.png\'' % (model, valid_folder),
                            'conda deactivate']
                cmd = '\n'.join(cmd_list)
                subprocess.run(cmd, shell=True)
                gt_files = [valid_folder + '/' + ele for ele in os.listdir(valid_folder) if ele.endswith('.gt.txt')]
                res_str = evaluate(gt_files)
                print(model, res_str)
                if float(res_str["char_error_rate"]) > best_perform:
                    best_perform = float(res_str["char_error_rate"])
                    best_model = index
                f_out.write('Iteration: %s, errors: %d, missing: %d, total: %d, char error rate: %s\n'
                            % (index, res_str["errors"], res_str["missing"], res_str["total"], res_str["char_error_rate"]))
            else:
                res_str = dict_res[int(index)]
                f_out.write('Iteration: %s, %s\n' % (res_str[1], res_str[0]))
            best_model_file = 'static/model/%s/%s-%s.pyrnn.gz' % (model_dir, model_prefix, best_model)
            dest_model_file = 'static/model/%s/best.pyrnn.gz' % model_dir
            print("Model %s is the best model" % best_model)
            copyfile(best_model_file, dest_model_file)
    elif engine == 'tesseract':
        model_name = model_prefix
        cmd_list = ['export TESSDATA_PREFIX=%s' % pjoin(os.getcwd(),
                                                        'static/model', model_dir)]
        convert_image('engines/eval')
        image_files = get_all_files(data_folder=valid_folder, postfix='.tif')
        for imf in image_files:
            cmd_list.append('tesseract -l %s %s/%s.tif %s/%s ' % (model_name,
                                                                  valid_folder,
                                                                  imf,
                                                                  valid_folder,
                                                                  imf))
    f_out.close()


eval_from_file(model_dir='31092911ae524c8a957147f7449e35cd', engine='ocropus', model_prefix='ocropus')