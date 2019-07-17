from engines.validate_parameters import read_parameter_from_schema
from engines.common import read_json
from engines.process_tesseract import *
from engines import data_folder, tmp_folder, act_environ, deact_environ
from engines.common import split_train_test
import numpy as np


def files2str(setname, catstr):
    a = []
    with open(pjoin(tmp_folder, 'list.%s' % setname)) as f_:
        for line in f_:
            a.append(line.strip())
    res_str = catstr.join(a)
    return res_str


class Translate:
    def __init__(self, file_config, model_dir):
        self.configs = read_json(pjoin('static/configs', file_config))
        self.engine = self.configs["engine"]
        self.model_dir = model_dir
        self.translator = read_json('engines/schemas/translate.json')[self.engine]
        self.default = read_parameter_from_schema(read_json('engines/schemas/%s.schema' % self.engine))
        self.model_prefix = self.get_value("model_prefix")
        self.nepoch = self.get_value('nepoch')
        partition = self.get_value('partition')
        self.ntrain, self.ntest = split_train_test(data_folder,
                                                   tmp_folder,
                                                   partition,
                                                   engine=self.engine)
        self.translate()
        self.cmd_list = [act_environ(self.engine)] + self.cmd_list + [deact_environ]\
            if self.engine != 'tesseract' else self.cmd_list

    def translate(self):
        method = getattr(self, self.engine, lambda: "Invalid Engine")
        return method()

    def get_value(self, key):
        return self.configs[key] if key in self.configs else self.default[key]

    def tesseract(self):
        model_folder = self.model_dir
        checkpoint_folder = pjoin(self.model_dir, 'checkpoint')
        preprocess(data_folder, tmp_folder, model_folder, checkpoint_folder, self.model_prefix)
        cmd = 'lstmtraining --traineddata %s --train_listfile %s ' %\
              (pjoin(model_folder, self.model_prefix, self.model_prefix + '.traineddata'),
               pjoin(tmp_folder, 'list.train'))
        if self.ntest > 0:
            cmd += '--eval_listfile %s ' % pjoin(tmp_folder, 'list.eval')

        max_iter = self.nepoch * self.ntrain
        cmd += '%s %d ' % (self.translator["nepoch"], max_iter)

        cmd += '%s %s ' % (self.translator['model_prefix'],
                           pjoin(checkpoint_folder, self.model_prefix))

        voc_size = get_numofchar(tmp_folder)
        for para in self.configs:
            if para in ['engine', 'partition', "model_prefix"]:
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
        cmd = 'ketos train -t %s -e %s ' % (pjoin(tmp_folder, 'list.train'),
                                                 pjoin(tmp_folder, 'list.eval'))

        cmd += '%s %s ' % (self.translator['model_prefix'],
                           pjoin(self.model_dir, self.model_prefix))

        cmd += '%s %d ' % (self.translator['nepoch'], self.nepoch)

        cmd += '%s %.1f ' % (self.translator['save_freq'], self.get_value('save_freq'))

        if 'early_stop' in self.configs:
            cmd += '%s early ' % self.translator['early_stop']
            if 'early_stop_min_improve' in self.configs:
                cmd += '%s %f ' % (self.translator['early_stop_min_improve'],
                                   self.configs['early_stop_min_improve'])
            if 'early_stop_nbest' in self.configs:
                cmd += '%s %d ' % (self.translator['early_stop_nbest'],
                                   self.configs['early_stop_nbest'])
        else:
            cmd += '%s dumb ' % self.translator['early_stop']

        cmd += '%s %f ' % (self.translator['learning_rate'],
                           self.get_value('learning_rate'))

        cmd += '%s \"%s\" ' % (self.translator['model_spec'], self.get_value('model_spec'))

        # for para in self.configs:
        #     if para in ['engine', 'early_stop', 'partition', 'nepoch']:
        #         continue
        #     if para == "preload":
        #         if self.configs[para]:
        #             cmd += '--preload '
        #         else:
        #             cmd += '--no-preload '
        #     elif para == 'continue_from':
        #         if len(self.configs[para]) > 0:
        #             cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        #     elif para == 'append':
        #         if "continues_from" in self.configs and len(self.configs["continue_from"]) > 0:
        #             cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        #     elif para == 'model_spec':
        #         cmd += '%s \"%s\" ' % (self.translator[para], self.configs[para])
        #     else:
        #         print(para)
        #         cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '

        print(cmd)
        self.cmd_list = [cmd]

    def ocropus(self):
        train_str = files2str('train', ' ')
        if self.ntest > 0:
            test_str = files2str('eval', ':')
            cmd = 'ocropus-rtrain %s -t %s ' % (train_str, test_str)
        else:
            cmd = 'ocropus-rtrain %s/*.png ' % data_folder

        max_iter = self.nepoch * self.ntrain

        cmd += '%s %d ' % (self.translator["nepoch"], max_iter)

        cmd += '%s %s ' % (self.translator['model_prefix'],
                           pjoin(self.model_dir, self.model_prefix))

        save_freq = int(self.get_value('save_freq') * self.ntrain)
        cmd += '%s %d ' % (self.translator['save_freq'], save_freq)

        model_spec = self.get_value('model_spec')[1:-1]
        direction = model_spec[0]
        hidden_size = int(model_spec[1:])
        if direction != 'b':
            cmd += '--unidirectional '
        cmd += '-S %d ' % hidden_size

        cmd += '%s %f ' % (self.translator['learning_rate'],
                           self.get_value('learning_rate'))


        # for para in self.configs:
        #     if para not in self.translator:
        #         if para in ["engine", "save_freq", "nepoch", "model_prefix"]:
        #             continue
        #         if para == "model_spec":
        #             value = self.configs[para][1:-1]
        #             direction = value[0]
        #             hidden_size = int(value[1:])
        #             if direction != 'b':
        #                 cmd += '--unidirectional '
        #             cmd += '-S %d ' % hidden_size
        #     else:
        #         cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        print(cmd)
        self.cmd_list = [cmd]

    def calamari(self):
        train_str = files2str('train', ' ')
        if self.ntest > 0:
            test_str = files2str('eval', ' ')
            cmd = 'calamari-train --files %s --validation %s ' % (train_str, test_str)
        else:
            cmd = 'calamari-train --files %s/*.png ' % data_folder

        batch_size = self.get_value('batch_size')
        cmd += '%s %d ' % (self.translator['batch_size'], batch_size)

        max_iter = self.nepoch * int(np.ceil(self.ntrain / batch_size))
        cmd += '%s %d ' % (self.translator['nepoch'], max_iter)

        cmd += '%s %.1f ' % (self.translator['save_freq'], self.get_value('save_freq'))

        cmd += '%s %s ' % (self.translator['model_prefix'], self.model_prefix)

        cmd += '--output_dir %s ' % self.model_dir

        model_spec = self.get_value('model_spec')
        items = model_spec[1:-1].split(' ')
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
        lrate = self.get_value('learning_rate')
        network += 'l_rate=%f' % lrate
        cmd += '--network %s ' % network.strip(',')

        # for para in self.configs:
        #     if para in ["engine", "nepoch", "batch_size", 'partition']:
        #         continue
        #     if para == 'no_skip_invalid_gt':
        #         if self.configs[para]:
        #             print(self.configs[para])
        #             cmd += '--no_skip_invalid_gt '
        #         continue
        #     if para == 'preload' or para == 'preload_test':
        #         if self.configs[para]:
        #             cmd += '%s ' % self.translator[para]
        #         continue
        #     if para not in self.translator:
        #         print(para)
        #         cmd += '--' + para + ' ' + str(self.configs[para]) + ' '
        #     else:
        #         if para == 'model_spec':
        #             value = self.configs[para]
        #             items = value[1:-1].split(' ')
        #             network = ''
        #             for ele in items:
        #                 if ele[0] == 'C':
        #                     print(ele)
        #                     subeles = ele[1:].split(',')
        #                     print(subeles)
        #                     network += "cnn=" + subeles[-1] + ':' + subeles[0] + 'x' + subeles[1] + ','
        #                 elif ele[:2] == 'Mp':
        #                     print(ele)
        #                     subeles = ele[2:].split(',')
        #                     network += "pool=" + subeles[0] + 'x' + subeles[1] + ','
        #                 elif ele[:2] == 'Do':
        #                     print(ele)
        #                     network += 'dropout=' + ele[2:] + ','
        #                 elif ele[0] == 'L':
        #                     print(ele)
        #                     network += 'lstm=' + ele[1:] + ','
        #             cmd += '--network %s ' % network.strip(',')
        #         elif para == 'continue_from':
        #             if len(self.configs["continue_from"]) > 0:
        #                 cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        #         else:
        #             cmd += self.translator[para] + ' ' + str(self.configs[para]) + ' '
        print(cmd)
        self.cmd_list = [cmd]

#
# def test():
#     configs = read_parameters('engines/schemas/sample.json')
#     print(configs)
#     translate = Translate(configs, model_dir='model')
