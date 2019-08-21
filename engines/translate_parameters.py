from engines.common import read_json
from engines.process_tesseract import *
from engines import data_folder, tmp_folder, valid_folder, data_root, model_root, config_root, act_environ, deact_environ
from engines.common import split_train_test
import numpy as np
from engines.translate_model import ModelTranslator, get_old_input_size
from  lib.file_operation import get_model_dir


def read_parameter_default(engine):
    common_schema = read_json("engines/schemas/common.schema")
    default_values = {}
    for key in common_schema["definitions"]:
        if common_schema["definitions"][key]["type"] != "object":
            default_values[key] = common_schema["definitions"][key]["default"]
    engine_schema = read_json("engines/schemas/engine_%s.schema" % engine)
    for key in engine_schema["properties"]:
        if "$ref" not in engine_schema["properties"][key]:
            if engine_schema["properties"][key]["type"] == "object":
                for ele in engine_schema["properties"][key]["properties"]:
                    new_key = '%s_%s' % (key, ele)
                    default_values[new_key] = engine_schema["properties"][key]["properties"][ele]["default"]
            else:
                default_values[key] = engine_schema["properties"][key]["default"]
    return default_values


def read_value(configs, engine):
    default_values = read_parameter_default(engine)
    values = {}
    for k in configs:
        if type(configs[k]) is dict:
            for ele in configs[k]:
                new_key = '%s_%s' % (k, ele)
                values[new_key] = configs[k][ele]
        else:
            values[k] = configs[k]
    for ele in default_values:
        if ele not in values:
            values[ele] = default_values[ele]
    return values

def translate_continue_path(engine, continue_from):
    model_dir = get_model_dir(continue_from["trainset"], continue_from["config"])
    if engine ==  'tesseract':
        return os.path.join(model_root,  model_dir, 'checkpoint', continue_from["model"])
    else:
        return os.path.join(model_root,  model_dir, continue_from["model"])

def get_old_traineddata(config):
    old_config_file = config["continue_from"]["config"]
    old_config = read_json(os.path.join(config_root, old_config_file))
    old_train  = config["continue_from"]["trainset"]
    old_model_dir =  get_model_dir(old_train, old_config_file)
    common_schema = read_json("engines/schemas/common.schema")
    old_model_prefix = old_config["model_prefix"] if "model_prefix" in old_config \
        else common_schema["definitions"]["model_prefix"]["default"]
    old_traineddata = os.path.join(model_root,  old_model_dir, old_model_prefix, old_model_prefix + '.traineddata')
    return old_traineddata

def process_kraken_reshape_size(config):
    old_model =  read_json(os.path.join(config_root, config["continue_from"]["config"]))["model"]
    input_size = get_old_input_size(old_model, config["append"])
    return input_size


class Translate:
    def __init__(self, file_config, model_dir):
        self.configs = read_json(pjoin(config_root, file_config))
        self.engine = self.configs["engine"]
        self.model_dir = model_dir

        self.translator = read_json('engines/schemas/translate.json')[self.engine]

        # load default values
        # self.default = read_parameter_default(self.engine)
        # replace default values with user specified values
        self.values = read_value(self.configs, self.engine)
        if "continue_from" in self.configs:
            self.values["continue_from"] = translate_continue_path(self.configs["engine"], self.configs["continue_from"])
        else:
            self.values["continue_from"] = ''
        self.model_translator = ModelTranslator(self.configs["model"], self.engine)

        self.model_prefix = self.values["model_prefix"]
        self.nepoch = self.values['nepoch']
        partition = self.values['partition']
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

    # def values(self, key):
    #     return self.configs[key] if key in self.configs else self.default[key]

    def tesseract(self):
        model_folder = self.model_dir
        checkpoint_folder = pjoin(self.model_dir, 'checkpoint')
        preprocess(data_folder, tmp_folder, model_folder, checkpoint_folder, self.model_prefix)
        # partition
        cmd = '/Users/doreen/Documents/Experiment/Package/tesseract/src/training/lstmtraining --traineddata %s --train_listfile %s ' %\
              (pjoin(model_folder, self.model_prefix, self.model_prefix + '.traineddata'),
               pjoin(tmp_folder, 'list.train'))
        if self.ntest > 0:
            cmd += '--eval_listfile %s ' % pjoin(tmp_folder, 'list.eval')


        # nepoch
        max_iter = int(self.nepoch * np.ceil(self.ntrain / self.values["batch_size"]))
        cmd += '--%s %d ' % (self.translator["nepoch"], max_iter)

        # model_prefix
        cmd += '--%s %s ' % (self.translator['model_prefix'],
                           pjoin(checkpoint_folder, self.model_prefix))


        # save_freq
        save_freq = np.floor(self.values["savefreq"] * self.ntrain)
        cmd += '--save_freq %d ' % save_freq

        # optimizer
        optimizer = self.values["optimizer"]
        if optimizer == 'Adam':
            cmd += '--net_mode %d ' % 192
        else:
            cmd += '--net_mode %d' % 128

        # append
        flag_append = False if self.values["append"] == -1 or len(self.values["continue_from"]) == 0 else True


        # model
        voc_size = get_numofchar(tmp_folder)
        cmd += '%s ' % self.model_translator.tesseract(self.values["batch_size"], flag_append, voc_size)
        floats = ["append", "continue_from",
                   "momentum", "adam_beta",
                  "target_error_rate",
                  "perfect_sample_delay"]

        for para in self.configs:
            if para not in floats:
                continue
            # elif para ==  'continue_from':
            #     old_trained_data = get_old_traineddata(self.configs)
            #     para_name = self.translator[para] if para in self.translator else para
            #     cmd  +=  '--%s %s --old_traineddata %s ' % (para_name, str(self.values[para]), old_trained_data)
            else:
                para_name = self.translator[para] if para in self.translator else para
                cmd += '--%s %s ' % (para_name, str(self.values[para]))
        print(cmd)
        self.cmd_list = ['export TESSDATA_PREFIX=/usr/local/share/tessdata',
                         cmd]

    def kraken(self):
        print(self.configs)
        # Partition
        cmd = 'ketos train -t %s -e %s ' % (pjoin(tmp_folder, 'list.train'),
                                                 pjoin(tmp_folder, 'list.eval'))
        # model_prefix
        cmd += '--%s %s ' % (self.translator['model_prefix'],
                           pjoin(self.model_dir, self.model_prefix))
        # nepoch
        cmd += '--%s %d ' % (self.translator['nepoch'], self.nepoch)
        # save_freq
        cmd += '--savefreq %.1f ' % self.values['savefreq']
        # learning_rate
        cmd += '--%s %f ' % (self.translator['learning_rate'], self.values['learning_rate'])
        # append
        flag_append = False if self.values["append"] == -1 or len(self.values["continue_from"]) == 0 else True

        # model
        if flag_append:
            input_size = process_kraken_reshape_size(self.configs)
        else:
            input_size = 0
        cmd += '%s ' % self.model_translator.kraken(self.values["batch_size"], flag_append, input_size=input_size)  # model specification

        # early stop
        if 'early_stop' in self.configs:
            cmd += '--%s early ' % self.translator['early_stop']
            if 'min_improve' in self.configs["early_stop"]:
                cmd += '--%s %f ' % (self.translator['early_stop_min_improve'],
                                   self.values['early_stop_min_improve'])
            if 'nbest' in self.configs["early_stop"]:
                cmd += '--%s %d ' % (self.translator['early_stop_nbest'],
                                   self.values['early_stop_nbest'])
        else:
            cmd += '--%s dumb ' % self.translator['early_stop']

        floats = ["append", "continue_from",
                  "optimizer", "momentum", "schedule", "weight_decay",
                  "preload", "device", "threads",
                  "normalization", "normalize-whitespace",
                  "codec", "resize", "reorder"]

        for para in self.configs:
            if para not in floats:
                continue
            para_name = self.translator[para] if para in self.translator else para
            if para in ['preload', 'reorder', "normalize-whitespace"]:
                if self.values[para]:
                    cmd += '--%s ' % para_name
                else:
                    cmd += '--no-%s' % para_name
            else:
                cmd += '--%s %s ' % (para_name, self.values[para])
        print(cmd)
        self.cmd_list = [cmd]

    def ocropus(self):
        # partition
        if self.ntest > 0:
            cmd = 'ocropus-rtrain %s/*.png -t \'%s/*.png\' ' % (data_folder, valid_folder)
        else:
            cmd = 'ocropus-rtrain %s/*.png ' % data_folder

        # nepoch
        max_iter = self.nepoch * self.ntrain
        cmd += '--%s %d ' % (self.translator["nepoch"], max_iter)

        # model_prefix
        cmd += '--%s %s ' % (self.translator['model_prefix'],
                           pjoin(self.model_dir, self.model_prefix))
        # save_freq
        save_freq = int(self.values['savefreq'] * self.ntrain)
        cmd += '--savefreq %d ' % save_freq

        # model
        cmd += '%s ' % self.model_translator.ocropus()

        # learning_rate
        cmd += '--%s %f ' % (self.translator['learning_rate'], self.values['learning_rate'])

        floats = ["start", "codec", "continue_from"]
        for para in self.configs:
            if para not in floats:
                continue
            para_name = self.translator[para] if para in self.translator else para
            if para == 'codec':
                cmd += '--%s %s' % (para_name, ' '.join(['\'' + ele + '\'' for ele in self.values[para]]))
            else:
                cmd += '--%s %s ' % (para_name, self.values[para])
        # print(cmd)
        self.cmd_list = [cmd.strip()]

    def calamari(self):
        # partition
        if self.ntest > 0:
            cmd = 'calamari-train --files %s/*.png --validation %s/*.png ' % (data_folder, valid_folder)
        else:
            cmd = 'calamari-train --files %s/*.png ' % data_folder

        # nepoch
        batch_size = self.values["batch_size"]
        max_iter = self.nepoch * int(np.ceil(self.ntrain / batch_size))
        cmd += '--%s %d ' % (self.translator['nepoch'], max_iter)

        # savefreq
        cmd += '--%s %.1f ' % (self.translator['savefreq'], self.values['savefreq'])

        # model_prefix
        if self.model_prefix[-1] != '_':
            self.model_prefix += '_'
        cmd += '--%s %s ' % (self.translator['model_prefix'], self.model_prefix)
        cmd += '--output_dir %s ' % self.model_dir

        # model
        cmd += self.model_translator.calamari(learning_rate=self.values["learning_rate"]) + ' '

        floats = ["continue_from", "stats_size", "seed",
                  "bidi_dir", "text_normalization", "text_regularization"
                  "continue_from",
                  "no_skip_invalid_gt",
                  "gradient_clipping_mode",
                  "gradient_clipping_const",
                  "backend"]
        floats_hier = ["early_stop", "num_threads", "preload"]
        for para in self.configs:
            if para not in floats and para not in floats_hier:
                continue
            if para in floats:
                if para == 'no_skip_invalid_gt':
                    if self.configs[para]:
                        cmd += '--no_skip_invalid_gt '
                else:
                    para_name = self.translator[para] if para in self.translator else para
                    cmd += '--%s %s ' % (para_name, str(self.values[para]))
            elif para in floats_hier:
                for ele in self.configs[para]:
                    fullname = '%s_%s' % (para, ele)
                    para_name = self.translator[fullname] if fullname in self.translator else fullname
                    if "preload" in fullname:
                        if self.values[fullname]:
                            cmd += '--%s ' % para_name
                    else:
                        cmd += '--%s %s ' % (para_name, str(self.values[fullname]))
        print(cmd)
        self.cmd_list = ['export KMP_DUPLICATE_LIB_OK=TRUE', cmd]


# def test():
#     translate = Translate('sample_tess_continue.json', model_dir='static/model/d2503a3a1e464338853fc5f7040febc7')
#     print('\n'.join(translate.cmd_list))
# #
# #
# test()
