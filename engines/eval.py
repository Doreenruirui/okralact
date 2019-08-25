from engines.validate_parameters import read_json
import subprocess
from os.path import join as pjoin
import os
import uuid
from lib.file_operation import compress_file, get_model_dir, clear_data, extract_file, read_list, write_list
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
        report_file = pjoin(eval_root, old_eval_file)
        if os.path.exists(report_file):
            os.remove(report_file)
        if os.path.exists(report_file  +  '.tar.gz'):
            os.remove(report_file + '.tar.gz')

    dict_eval[key] = uni_model_dir
    write_list(eval_file, dict_eval)
    return dict_eval[key]


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
    if engine == 'tesseract':
        best_model = pjoin(model_root, model_dir, 'checkpoint', model_file)
    else:
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
    print(cmd_list)
    subprocess.run(cmd, shell=True)
    gt_files = [eval_folder + '/' + ele for ele in os.listdir(eval_folder) if ele.endswith('.gt.txt')]
    if engine == 'calamari':
        res = evaluate(gt_files,  flag_confusion=1, extension='.pred.txt')
        res_files = [os.getcwd()  +  '/' +  ele[:-len(".gt.txt")] +  '.pred.txt' for ele in gt_files]
    else:
        res = evaluate(gt_files, flag_confusion=1)
        res_files = [os.getcwd()  +  '/' + ele[:-len(".gt.txt")] +  '.txt' for ele in gt_files]
    report_file = add_eval_report(file_test, file_train, file_config, model_file)
    out_file =  pjoin(os.getcwd(), eval_root, report_file  +  '.tar.gz')
    compress_file(res_files,  out_file)
    with open(pjoin(eval_root, report_file), 'w') as f_:
        f_.write('\nTotal characters:\t%d\n' % res["char_total"])
        f_.write('Character errors:\t%d\n' % res["char_errs"])
        f_.write('Character error rate:\t%.3f\n' % res["char_error_rate"])
        f_.write('Total words:\t%d\n' % res["word_total"])
        f_.write('Word errors:\t%d\n' % res["word_errs"])
        f_.write('Word error rate:\t%.3f\n\n\n' % res["word_error_rate"])
        f_.write('count\tcorrect\tgenerated\n')
        for v, a, b  in res["confusion"]:
            f_.write("%d\t%s\t%s\n" % (v, a, b))
    return report_file


# eval_from_file(file_test='test_10.tar.gz', file_train='train_500.tar.gz', file_config='sample_calamari.json', model_file='model_00004500.ckpt')
# compress_file(res_files,  out_file)

