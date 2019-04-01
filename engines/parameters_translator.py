from os.path import join as pjoin
import json
from engines.validate_parameters import read_json, read_parameters


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

    def kraken(self):
        cmd = 'ketos train engines/data/*.png '
        for para in self.configs:
            if para not in self.translator:
                print(para)
                if para == "preload":
                    if self.configs[para]:
                        cmd += '--preload '
                    else:
                        cmd += '--no-preload '
            else:
                if para == 'model_prefix':
                    cmd += self.translator[para] + ' ' + pjoin(self.model_dir, self.configs[para]) + ' '
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
