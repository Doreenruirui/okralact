from os.path import join as pjoin
import json
from validate_parameters import read_json, read_parameters


def kraken(configs, model_dir):
    translator = read_json('engines/schemas/translate.json')["kraken"]
    cmd = 'ketos train ./data/*.png '
    for para in configs:
        if para not in translator:
            print(para)
            if para == "preload":
                if configs[para]:
                    cmd += '--preload '
                else:
                    cmd += '--no-preload '
        else:
            if para == 'model_prefix':
                cmd += translator[para] + ' ' + pjoin(model_dir, configs[para]) + ' '
            elif para == 'early_stop':
                cmd += translator[para] + ' early '
            elif para == 'continue_from':
                if len(configs[para]) > 0:
                    cmd += translator[para] + ' ' + str(configs[para]) + ' '
            elif para == 'append':
                if "continues_from" in configs and len(configs["continue_from"]) > 0:
                    cmd += translator[para] + ' ' + str(configs[para]) + ' '
            elif para == 'model_spec':
                cmd += ('%s \"%s\" ' % (translator[para], configs[para]))
            else:
                cmd += translator[para] + ' ' + str(configs[para]) + ' '
    print(cmd)
    return ['source activate kraken', cmd, 'source deactivate']


def ocroupus(configs, model_dir):
    translator = read_json('engines/schemas/translate.json')["ocropus"]
    cmd = 'ocropus-train ./data/*.png '
    for para in configs:
        if para not in translator:
            if para == "model_spec":
                value = configs[para][1:-1]
                direction = value[0]
                hidden_size = int(value[1:])
                if direction != 'b':
                    cmd += '--unidirectional '
                cmd += '-S %d ' % hidden_size
        else:
            if para == 'model_prefix':
                cmd += translator[para] + ' ' + pjoin(model_dir, configs[para]) + ' '
            else:
                cmd += translator[para] + ' ' + str(configs[para]) + ' '
    print(cmd)


def calamari(configs, model_dir):
    translator = read_json('engines/schemas/translate.json')['calamari']
    cmd = 'calamari-train --files ./data/*.png '
    for para in configs:
        if para not in translator:
            print(para)
            cmd += '--' + para + ' ' + str(configs[para]) + ' '
        else:
            if para == 'model_prefix':
                cmd += translator[para] + ' ' + str(configs[para]) + ' '
                cmd += '--output_dir ' + model_dir + ' '
            elif para == 'model_spec':
                value = configs[para]
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
                cmd += '--network %s ' + network.strip(',')
            elif para == 'continue_from' and len(configs["continue_from"]) > 0:
                print(configs[para])
                cmd += translator[para] + ' ' + str(configs[para]) + ' '
            else:
                cmd += translator[para] + ' ' + str(configs[para]) + ' '
    print(cmd)

configs = read_parameters('engines/schemas/sample.json')
print(configs)
calamari(configs, model_dir='model')