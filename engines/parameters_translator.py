from os.path import join as pjoin


class Translator:
    def __init__(self, configs, engine):
        self.configs = configs
        self.new_configs = {}
        self.cmd = ''
        func = getattr(self, engine)
        func()

    def kraken(self):
        self.new_configs['-o'] = pjoin(self.configs.model_dir, self.configs.model_prefix)
        self.new_configs['-N'] = self.configs.nepoch
        self.new_configs['-i'] = self.configs.continue_from
        self.new_configs['-a'] = self.configs.append
        self.new_configs['-r'] = self.configs.learning_rate
        if self.configs.early_stop:
            self.new_configs['-q'] = ''
            self.new_configs['--min-delta'] = self.configs.early_stop_min_improve
            self.new_configs['--lag'] = self.configs.early_stop_nbest
        self.new_configs['-d'] = self.configs.device
        self.new_configs['-s'] = self.configs.model_spec
        self.new_configs['-m'] = self.configs.momentum
        self.new_configs['-w'] = self.configs.weight_decay
        self.new_configs['--optimizer'] = self.configs.optimizer
        self.new_configs['-p'] = self.configs.partition
        if self.configs.preload:
            self.new_configs['--preload'] = ''
        else:
            self.new_configs['--no-preload'] = ''
        self.new_configs['--save_freq'] = self.configs.save_freq
        parameters = ['--' + ele + ' ' + str(self.new_configs[ele]) for ele in self.new_configs.keys()]
        self.cmd = 'ketos train ./data/*.png %s ' + ' '.join(parameters)

