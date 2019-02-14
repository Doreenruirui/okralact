### Todo: Show all the help info

# from parameters import configs
from config import Config
import subprocess
from os.path import join as pjoin
import os
import sys


class ENGINE(object):
    def __init__(self, engine_name, paras):
        self.name = engine_name
        self.paras = paras

    def run(self):
        method = getattr(self, self.name, lambda:"Invalid Engine")
        return method()

    def kraken(self):
        filename = self.paras.data_dir
        prefix = filename.rsplit('.', 2)[0]
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix)
        print('loading kraken ...')
        cmd_list = []
        cmd_list.append('source activate kraken')
        cmd_list.append('ketos train %s/*.png -o %s -N %d' % (prefix, model_prefix, self.paras.nepoch))
        cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)

    def ocropus(self):
        filename = self.paras.data_dir
        prefix = filename.rsplit('.', 2)[0]
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix)
        print('loading ocropus ...')
        nfiles = int(subprocess.check_output('ls data/*.png | wc -l', shell=True).strip())
        print(nfiles)
        cmd_list = []
        cmd_list.append('source activate ocropus_env')
        cmd_list.append('ocropus-rtrain %s/*.png -o %s -N %d' % (prefix, model_prefix, self.paras.nepoch * nfiles))
        cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)

    def tesseract(self):
        return 'loading tesseract ...'

    def calamari(self):
        filename = self.paras.data_dir
        prefix = filename.rsplit('.', 2)[0]
        model_prefix = pjoin(self.paras.model_dir, self.paras.prefix + '_')
        print('loading ocropus ...')
        nfiles = int(subprocess.check_output('ls data/*.png | wc -l', shell=True).strip())
        print(nfiles)
        cmd_list = []
        cmd_list.append('source activate calamari')
        cmd_list.append('calamari-train --files %s/*.png --output_model_prefix %s --batch_size 1 --max_iters %d' % (prefix, model_prefix, self.paras.nepoch * nfiles))
        cmd_list.append('source deactivate')
        print(cmd_list)
        cur_cmd = '\n'.join(cmd_list)
        subprocess.run(cur_cmd, shell=True)


def train(paras):
    engine = paras.engine
    # print('tar -zvcf ../static/data/%s' % filename)
    # subprocess.run('tar -zvxf ../static/data/%s' % filename, shell=True)
    print('You have chosen engine %s' % engine)
    engine = ENGINE(engine, paras)
    engine.run()


def train_from_file(config_file):
    configs = Config(config_file)
    configs.model_dir = pjoin('/Users/ruidong/Documents/Experiment/OCRD/engines', configs.model_dir)
    configs.data_dir = pjoin('/Users/ruidong/Documents/Experiment/OCRD/engines', configs.data_dir)
    train(configs)


if __name__ == "__main__":
    print(sys.argv[1])
    configs = Config(sys.argv[1])
    print(configs.model_dir)
    train(configs)

