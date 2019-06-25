from engines.validate_parameters import read_json, read_parameters
from engines.process_tesseract import *
from engines import data_folder, tmp_folder
from engines.common import split_train_test


class Translate:
    def __init__(self, configs, model_dir):
        self.configs = configs
        self.engine = configs["engine"]
        self.model_dir = model_dir
        self.translator = read_json('engines/schemas/translate.json')[self.engine]
        if 'partition' in configs and configs['partition'] < 1.0:
            partition = configs['partition']
        else:
            partition = 0.9
        self.ntrain, self.ntest = split_train_test(data_folder, tmp_folder, partition, engine=configs["engine"])
        if 'model_prefix' in self.configs:
            self.model_prefix = self.configs['model_prefix']
        else:
            self.model_prefix = self.engine
        self.translate()

    def translate(self):
        method = getattr(self, self.engine, lambda: "Invalid Engine")
        return method()

    def tesseract(self):
        model_folder = self.model_dir
        checkpoint_folder = pjoin(self.model_dir, 'checkpoint')
        preprocess(data_folder, tmp_folder, model_folder, checkpoint_folder, self.model_prefix)
        cmd = 'lstmtraining --traineddata %s --train_listfile %s ' %\
              (pjoin(model_folder, self.model_prefix, self.model_prefix + '.traineddata'),
               pjoin(tmp_folder, 'list.train'))
        # if self.ntest > 0:
        #     cmd += '--eval_listfile %s ' % pjoin(tmp_folder, 'list.eval')
        cmd += self.translator['model_prefix'] + ' ' + pjoin(checkpoint_folder, self.model_prefix) + ' '
        voc_size = get_numofchar(tmp_folder)
        for para in self.configs:
            if para in ['engine', 'partition']:
                continue
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
        self.cmd_list = [cmd,
                         'lstmtraining --stop_training --continue_from %s --traineddata %s --model_output %s' %
                         (pjoin(checkpoint_folder, self.model_prefix + '_checkpoint'),
                          pjoin(model_folder, self.model_prefix, self.model_prefix + '.traineddata'),
                          pjoin(model_folder, self.model_prefix + '.traineddata'))]

    def kraken(self):
        print(self.configs)
        cmd = 'ketos train -t %s ' % pjoin(tmp_folder, 'list.train')
        cmd += '-e %s ' % pjoin(tmp_folder, 'list.eval')
        cmd += self.translator['model_prefix'] + ' ' + pjoin(self.model_dir, self.model_prefix) + ' '
        if 'early_stop' in self.configs:
            cmd += '%s early ' % self.translator['early_stop']
            if 'early_stop_min_improve' in self.configs:
                cmd += '%s %f ' % (self.translator['early_stop_min_improve'], self.configs['early_stop_min_improve'])
            if 'early_stop_nbest' in self.configs:
                cmd += '%s %d ' % (self.translator['early_stop_nbest'], self.configs['early_stop_nbest'])
        else:
            cmd += '%s dumb ' % self.translator['early_stop']
        for para in self.configs:
            if para in ['engine', 'early_stop', 'partition']:
                continue
            if para == "preload":
                if self.configs[para]:
                    cmd += '--preload '
                else:
                    cmd += '--no-preload '
            elif para == 'continue_from':
                if len(self.configs[para]) > 0:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'append':
                if "continues_from" in self.configs and len(self.configs["continue_from"]) > 0:
                    cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
            elif para == 'model_spec':
                cmd += ('%s \"%s\" ' % (self.translator[para], self.configs[para]))
            else:
                print(para)
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
