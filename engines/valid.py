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
from engines import valid_folder
from shutil import copyfile
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
    with open(pjoin('static/model', model_dir, 'report')) as f_:
        for line in f_:
            print(line)
            if len(line) > 0:
                model_name, eval_res = line.split(',', 1)
                dict_res[int(model_name.split(':')[1].strip())] = eval_res
    # print(dict_res)
    return dict_res


def eval_from_file(model_dir, file_config):
    creat_valid()
    configs = read_json(pjoin('static/configs', file_config))
    print(configs)
    # noinspection PyInterpreter
    dict_res = read_report(model_dir)
    print(dict_res)
    f_out = open(pjoin('static/model', model_dir, 'report'), 'w')
    if configs["engine"] == 'kraken':
        models = [ele for ele in os.listdir('static/model/%s' % model_dir) if ele.endswith('.mlmodel')]
        if len(models) == 0:
            return 'No model yet.'
        model_postfixes = sorted([int(ele.split('.')[0].split('_')[1]) for ele in models])
        model_prefix = models[0].split('.')[0].split('_')[0]
        for index in model_postfixes:
            if index not in dict_res:
                model = model_prefix + '_' + str(index) + '.mlmodel'
                cmd_list = ['source activate kraken',
                            'kraken -I \'%s/*.png\' -o .txt ocr -m static/model/%s/%s -s'
                            % (valid_folder, model_dir, model),
                            'conda deactivate']
                cmd = '\n'.join(cmd_list)
                # print(cmd)
                subprocess.run(cmd, shell=True)
                gt_files = [valid_folder + '/' + ele for ele in os.listdir(valid_folder) if ele.endswith('.gt.txt')]
                res_str = evaluate(gt_files)
                print(model, res_str)
                f_out.write('epoch: %d, errors: %d, missing: %d, total: %d, char error rate: %s\n' % (index,
                                                                                                  res_str["errors"],
                                                                                                  res_str["missing"],
                                                                                                  res_str["total"],
                                                                                      res_str["char_error_rate"]))
            else:
                res_str = dict_res[index]
                f_out.write('epoch %d, %s' % (index, res_str))
    elif configs["engine"] == 'calamari':
        with open('static/model/%s/checkpoint' % model_dir) as f_:
            model_file = f_.readlines()[0].split('"')[1]
        cmd_list = ['source activate calamari',
                    'calamari-predict --checkpoint %s --files %s/*.png' % (model_file, valid_folder),
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
        cmd_list.append('ocropus-rpred -m %s \'%s/*.png\'' % (model_file, valid_folder))
        cmd_list.append('conda deactivate')
    elif configs["engine"] == 'tesseract':
        if "model_prefix" in configs:
            model_name = configs["model_prefix"]
        else:
            model_name = configs["engine"]
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


# read_report(model_dir='model')
#
eval_from_file( model_dir='4347d9970c914a07a549ef8b5d64690e', file_config='sample_kraken.json')