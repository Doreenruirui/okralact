import json
import sys
import subprocess


def process_config(config_file):
    with open(config_file) as f:
        configs = json.load(f)
        parameters = ['--' + ele + ' ' + str(configs[ele]) for ele in configs.keys() if ele != 'engine']
        cmd = 'python train.py %s ' % configs['engine'] + ' '.join(parameters)
        # cmd += ' --model_spec \'' + configs['model_spec'] + '\''
        print(cmd)
        subprocess.run(cmd, shell=True)


process_config(sys.argv[1])


