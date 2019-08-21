from engines.common import read_json
import numpy as np


def read_layer_default(layername):
    layer_schema = read_json("engines/schemas/models/layer_%s.schema" % layername)
    default_values = {}
    for key in layer_schema["definitions"]:
        default_values[key] = layer_schema["definitions"][key]["default"]
    return default_values

def get_old_input_size(old_model, append):
    def get_pool_dim(input_size, kernel_size, stride_size):
        return int(np.floor((input_size - (kernel_size - 1) - 1) / stride_size + 1))
    old_model = [{"input": read_layer_default("input")}] + old_model \
                if "input" not in old_model[0] else old_model
    new_model = old_model[:append + 1]
    input_size = new_model[0]["input"]["height"]
    for cur_layer in new_model:
        for layer_name in cur_layer:
            values = read_layer_default(layer_name)                        # Get default value for each layer attribute
            layer = cur_layer[layer_name]
            values = {k: layer[k] if k in layer else values[k] for k in values} # Rewrite value according to user specific configuration
            if layer_name == "pooling":
                input_size = get_pool_dim(input_size, values["height"], values["y_stride"])
    return input_size

class ModelTranslator:
    def __init__(self, model, engine):
        self.model = model
        self.engine = engine
        self.translator = read_json("engines/schemas/models/translate_model.json")
        # self.model_str = self.translate()

    def kraken(self, batch_size, flag_append=False, input_size=0):
        def get_pool_dim(input_size, kernel_size, stride_size):
            return int(np.floor((input_size - (kernel_size - 1) - 1) / stride_size + 1))
        model_str = []
        if not flag_append:
            self.model = [{"input": read_layer_default("input")}] + self.model \
                if "input" not in self.model[0] else self.model
            input_size = self.model[0]["input"]["height"]
        flag_reshape = 0
        for cur_layer in self.model:
            for layer_name in cur_layer:
                values = read_layer_default(layer_name)                        # Get default value for each layer attribute
                layer = cur_layer[layer_name]
                values = {k: layer[k] if k in layer else values[k] for k in values} # Rewrite value according to user specific configuration
                if layer_name == "input":
                    layer_str = '%d,%d,%d,%d' % (batch_size,
                                                 values["height"],
                                                 values["width"],
                                                 values["channel"])
                elif layer_name == "cnn":
                    layer_str = 'C%s%d,%d,%d' % (self.translator[values["activation"]],
                                                 values["height"],
                                                 values["width"],
                                                 values["output"])
                elif layer_name == "rnn":
                    if not flag_reshape:
                        flag_reshape =  1
                        model_str.append('S1(1x%d)1,3' % input_size)
                    sum_str = 's' if values["sum"] else ''
                    layer_str = '%s%s%s%s%d' % (self.translator[values["cell"]],        # lstm or gru
                                                self.translator[values["direction"]],   # forward, backward or bidirectional
                                                values["time_axis"],
                                                sum_str,
                                                values["output"])
                elif layer_name == "reshape":
                    layer_str = 'S%d(%dx%d)%d,%d' % (values["dim"],
                                                     values["a"],
                                                     values["b"],
                                                     values["dim_e"],
                                                     values["dim_f"])
                    flag_reshape = 1
                elif layer_name == "pooling":
                    layer_str = 'Mp%d,%d,%d,%d' % (values["height"],
                                                   values["width"],
                                                   values["y_stride"],
                                                   values["x_stride"])
                    input_size = get_pool_dim(input_size, values["height"], values["y_stride"])

                elif layer_name == "dropout":
                    layer_str = "Do%.2f,%d" % (values["prob"], values["dim"])
                # elif layer_name == "output":
                    # layer_str = "O%d%s%d" % (values["type"], values["CTC"], values["size"])
                else:
                    raise "Layer %s not defined." % layer_name
                model_str.append(layer_str)
        return '--spec \'[' + ' '.join(model_str) + ']\''

    def ocropus(self):      # ocoropus only allow user specific rnn layer
        if len(self.model) > 0:
            model_str = []
            self.model = [{"input": read_layer_default("input")}] + self.model \
                if "input" not in self.model[0] else self.model
            input_layer = self.model[0]["input"]
            model_str.append('--height %d' % input_layer["height"])
            rnn_layer = self.model[1]["rnn"]
            values = read_layer_default("rnn")
            output = rnn_layer["output"] if "output" in rnn_layer else values["output"]
            direct = rnn_layer["direction"] if "direction" in rnn_layer else values["direction"]
            if direct != "bidirectional":
                model_str.append('--unidirectional')
            model_str.append('--hiddensize %d' % output)
            return ' '.join(model_str)
        else:
            return ''

    def calamari(self, learning_rate=0.001):
        model_str = []
        if "input" not in self.model[0]:
            input_layer = read_layer_default("input")
            model_str.append('--line_height %d' % input_layer["height"])
        for cur_layer in self.model:
            for layer_name in cur_layer:
                layer = cur_layer[layer_name]
                values = read_layer_default(layer_name)  # Get default value for each layer attribute
                values = {k: layer[k] if k in layer else values[k] for k in
                          values}  # Rewrite value according to user specific configuration
                if layer_name == "input":
                    layer_str = '--line_height %d' % values["height"]
                elif layer_name == "cnn":
                    layer_str = 'cnn=%d:%dx%d' % (values["output"],
                                                  values["height"],
                                                  values["width"])
                elif layer_name == "rnn":
                    layer_str = 'lstm=%d' % (values["output"])
                elif layer_name == "pooling":
                    layer_str = 'pool=%dx%d:%dx%d' % (values["height"],
                                                      values["width"],
                                                      values["y_stride"],
                                                      values["x_stride"])
                elif layer_name == "dropout":
                    layer_str = "dropout=%.2f" % values["prob"]
                else:
                    raise "Layer %s not defined." % layer_name
                model_str.append(layer_str)
        model_str.append('l_rate=%f' % learning_rate)
        return '%s --network=%s' % (model_str[0], ','.join(model_str[1:]))

    def tesseract(self, batch_size, flag_append=False, voc_size=100):
        model_str = []
        if not flag_append:
            self.model = [{"input": read_layer_default("input")}] + self.model \
                if "input" not in self.model[0] else self.model
        for cur_layer in self.model:
            for layer_name in cur_layer:
                values = read_layer_default(layer_name)  # Get default value for each layer attribute
                layer = cur_layer[layer_name]
                values = {k: layer[k] if k in layer else values[k] for k in
                          values}  # Rewrite value according to user specific configuration
                if layer_name == "input":
                    layer_str = '%d,%d,%d,%d' % (batch_size,
                                                 values["height"],
                                                 values["width"],
                                                 values["channel"])
                elif layer_name == "cnn":
                    layer_str = 'C%s%d,%d,%d' % (self.translator[values["activation"]],
                                                 values["height"],
                                                 values["width"],
                                                 values["output"])
                elif layer_name == "rnn":
                    sum_str = 's' if values["sum"] else ''
                    layer_str = 'L%s%s%s%d' % (self.translator[values["direction"]],
                                               values["time_axis"],
                                               sum_str,
                                               values["output"])
                elif layer_name == "pooling":
                    layer_str = 'Mp%d,%d' % (values["height"], values["width"])
                # elif layer_name == "output":
                #     voc_size = voc_size if "size" not in layer else values["size"]
                #     layer_str = "O%d%s%d" % (values["type"], values["CTC"], voc_size)
                else:
                    raise "Layer %s not defined." % layer_name
                model_str.append(layer_str)
        if "output" not in self.model[-1]:
            values = read_layer_default("output")
            print(values["type"], values["CTC"], voc_size)
            # layer_str = "O%d%s" % (values["type"], values["CTC"])
            layer_str = "O%d%s%d" % (values["type"], values["CTC"], voc_size)
            model_str.append(layer_str)
        return '--net_spec \'[' + ' '.join(model_str) + ']\''

#
# model = read_json('static/configs/sample_calamari.json')["model"]
# translator = ModelTranslator(model, 'calamari')
# print(translator.tesseract())
