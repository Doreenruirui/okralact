from os.path import join as pjoin
import json
from engines.validate_parameters import read_json, read_parameters
from engines.train_tesseract import *


class Folders:
    def __init__(self, model_dir):
        self.tmp_folder = 'engines/tmp'
        self.data_folder = 'engines/data'
        self.model_folder = model_dir
        self.checkpoint_folder = pjoin(model_dir, 'checkpoint')


class Translate:
    def __init__(self, configs, model_dir):
        self.configs = configs
        self.engine = configs["engine"]
        self.model_dir = model_dir
        self.translator = read_json('engines/schemas/translate.json')[self.engine]
        self.translate()

    def translate(self):
        method = getattr(self, self.engine, lambda: "Invalid Engine")
        return method()

    def tesseract(self):
        if 'model_prefix' in self.configs:
            model_prefix = self.configs['model_prefix']
        else:
            model_prefix = self.engine
        folders = Folders(self.model_dir)
        preprocess(folders, model_prefix)
        if 'partition' in self.configs:
            partition = self.configs['partition']
        else:
            partition = 0.9
        split_train_test(folders, train_ratio=partition)
        cmd = 'lstmtraining --traineddata %s --train_listfile %s --eval_listfile %s --learning_rate 0.001 ' %\
              (pjoin(folders.model_folder, model_prefix, model_prefix + '.traineddata'),
               pjoin(folders.tmp_folder, 'list.train'),
               pjoin(folders.tmp_folder, 'list.eval'))
        cmd += self.translator['model_prefix'] + ' ' + pjoin(folders.checkpoint_folder, model_prefix) + ' '
        voc_size = get_numofchar(folders)
        for para in self.configs:
            if para in ['engine', 'partition']:
                continue
            # elif para == 'continue_from':
            #   cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'append':
                cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'model_spec':
                if para.split(' ')[-1].startswith('O'):
                    model_spec = self.configs[para].rsplit(' ', 1)[0] + ' O1c' + str(voc_size) + ']'
                    print(model_spec)
                else:
                    model_spec = self.configs[para]
                cmd += ('%s \"%s\" ' % (self.translator[para], model_spec))
            else:
                cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        print(cmd)
        self.cmd_list = [cmd]

    def kraken(self):
        cmd = 'ketos train engines/data/*.png '
        if 'model_prefix' in self.configs:
            model_prefix = self.configs['model_prefix']
        else:
            model_prefix = self.engine
        cmd += self.translator['model_prefix'] + ' ' + pjoin(self.model_dir, model_prefix) + ' '
        for para in self.configs:
            if para == 'engine':
                continue
            if para == "preload":
                if self.configs[para]:
                    cmd += '--preload '
                else:
                    cmd += '--no-preload '
            elif para == 'early_stop':
                cmd += self.translator[para] + ' early '
            elif para == 'continue_from':
                if len(self.configs[para]) > 0:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'append':
                if "continues_from" in self.configs and len(self.configs["continue_from"]) > 0:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'model_spec':
                cmd += ('%s \"%s\" ' % (self.translator[para], self.configs[para]))
            else:
                cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '

        print(cmd)
        self.cmd_list = ['source activate kraken', cmd, 'conda deactivate']

    def ocropus(self):
        cmd = 'ocropus-rtrain engines/data/*.png '
        if 'model_prefix' in self.configs:
            model_prefix = self.configs['model_prefix']
        else:
            model_prefix = self.engine
        cmd += self.translator['model_prefix'] + ' ' + pjoin(self.model_dir, model_prefix) + ' '
        if 'save_freq' in self.configs:
            save_freq = self.configs['save_freq']
        else:
            save_freq = 50
        cmd += self.translator['save_freq'] + ' ' + str(save_freq) + ' '
        for para in self.configs:
            if para not in self.translator:
                if para == "engine":
                    continue
                if para == "model_spec":
                    value = self.configs[para][1:-1]
                    direction = value[0]
                    hidden_size = int(value[1:])
                    if direction != 'b':
                        cmd += '--unidirectional '
                    cmd += '-S %d ' % hidden_size
            else:
                if para == 'model_prefix':
                    cmd += self.translator[para] + ' ' + pjoin(self.model_dir, self.configs[para]) + ' '
                else:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        print(cmd)
        self.cmd_list = ['source activate ocropus_env', cmd, 'conda deactivate']

    def calamari(self):
        cmd = 'calamari-train --files engines/data/*.png '
        for para in self.configs:
            if para == "engine":
                continue
            if para == 'no_skip_invalid_gt':
                if self.configs[para]:
                    print(self.configs[para])
                    cmd += '--no_skip_invalid_gt '
                continue
            if para == 'partition':
                continue
            if para == 'preload' or para == 'preload_test':
                if self.configs[para]:
                    cmd += '%s ' % self.translator[para]
                continue
            if para not in self.translator:
                print(para)
                cmd += '--' + para + ' ' + str(self.configs[para]) + ' '
            else:
                if para == 'model_prefix':
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
                    cmd += '--output_dir ' + self.model_dir + ' '
                elif para == 'model_spec':
                    value = self.configs[para]
                    items = value[1:-1].split(' ')
                    network = ''
                    for ele in items:
                        if ele[0] == 'C':
                            print(ele)
                            subeles = ele[1:].split(',')
                            print(subeles)
                            network += "cnn=" + subeles[-1] + ':' + subeles[0] + 'x' + subeles[1] + ','
                        elif ele[:2] == 'Mp':
                            print(ele)
                            subeles = ele[2:].split(',')
                            network += "pool=" + subeles[0] + 'x' + subeles[1] + ','
                        elif ele[:2] == 'Do':
                            print(ele)
                            network += 'dropout=' + ele[2:] + ','
                        elif ele[0] == 'L':
                            print(ele)
                            network += 'lstm=' + ele[1:] + ','
                    cmd += '--network %s ' % network.strip(',')
                elif para == 'continue_from':
                    if len(self.configs["continue_from"]) > 0:
                        cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
                else:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        print(cmd)
        self.cmd_list = ['source activate calamari', cmd, 'conda deactivate']

#
# def test():
#     configs = read_parameters('engines/schemas/sample.json')
#     print(configs)
#     translate = Translate(configs, model_dir='model')
