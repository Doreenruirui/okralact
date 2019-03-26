from os.path import join as pjoin
import json
from validate_parameters import read_json, read_parameters


def kraken(configs, model_dir):
    translator = read_json('engines/schemas/kraken_translate.json')
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

configs = read_parameters('engines/schemas/sample.json')
print(configs)
kraken(configs, model_dir='model')