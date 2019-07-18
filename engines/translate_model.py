from engines.common import read_json
import numpy as np


def read_layer_default(layername):
    layer_schema = read_json("engines/schemas/models/layer_%s.schema" % layername)
    default_values = {}
    for key in layer_schema["definitions"]:
        default_values[key] = layer_schema["definitions"][key]["default"]
    return default_values


class ModelTranslator:
    def __init__(self, model, engine):
        self.model = model
        self.engine = engine
        self.translator = read_json("engines/schemas/models/translate_model.json")
        # self.model_str = self.translate()

    def kraken(self, batch_size):
        def get_pool_dim(input_size, kernel_size, stride_size):
            return int(np.floor((input_size - (kernel_size - 1) - 1) / stride_size + 1))
        model_str = []
        self.model = [read_layer_default("input")] + self.model if self.model[0]["name"] != "input" else self.model
        input_size = self.model[0]["height"]
        for layer in self.model:
            layer_name = layer["name"]
            values = read_layer_default(layer_name)                        # Get default value for each layer attribute
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
                sum_str = 's' if values["sum"] else ''
                layer_str = '%s%s%s%s%d' % (self.translator[values["cell"]],        # lstm or gru
                                            self.translator[values["direction"]],   # forward, backward or bidirectional
                                            values["time_axis"],
                                            sum_str,
                                            values["output"])
            elif layer_name == "reshape":
                layer_str = 'S%d(%dx%d)%d,%d' % (values["dim"],
                                                 values["a"],
                                                 input_size,
                                                 values["dim_e"],
                                                 values["dim_f"])
            elif layer_name == "pooling":
                layer_str = 'Mp%d,%d,%d,%d' % (values["height"],
                                               values["width"],
                                               values["y_stride"],
                                               values["x_stride"])
                input_size = get_pool_dim(input_size, values["height"], values["y_stride"])

            elif layer_name == "dropout":
                layer_str = "Do%.2f,%d" % (values["prob"], values["dim"])
            elif layer_name == "output":
                layer_str = "O%d%s%d" % (values["type"], values["CTC"], values["size"])
            else:
                raise "Layer %s not defined." % layer_name
            model_str.append(layer_str)
        return '--spec \'[' + ' '.join(model_str) + ']\''

    def ocropus(self):      # ocoropus only allow user specific rnn layer
        if len(self.model) > 0:
            rnn_layer = self.model[0]["rnn"]
            values = read_layer_default("rnn")
            model_str = []
            output = rnn_layer["output"] if "output" in rnn_layer else values["output"]
            direct = rnn_layer["direction"] if "direction" in rnn_layer else values["direction"]
            if direct != "bidirectional":
                model_str.append('--unidirectional')
            model_str.append('--hidden_size %d' % output)
            return ' '.join(model_str)
        else:
            return ''

    def calamari(self, learning_rate=0.001):
        model_str = []
        if self.model[0]["name"] != "input":
            input_layer = read_layer_default("input")
            model_str.append('--line_height %d' % input_layer["height"])
        for layer in self.model:
            layer_name = layer["name"]
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

    def tesseract(self, batch_size, voc_size):
        model_str = []
        if self.model[0]["name"] != "input":
            input_layer = read_layer_default("input")
            input_layer["name"] = "input"
            self.model = [input_layer] + self.model
        for layer in self.model:
            layer_name = layer["name"]
            values = read_layer_default(layer_name)  # Get default value for each layer attribute
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
            elif layer_name == "output":
                voc_size = voc_size if "size" not in layer else values["size"]
                layer_str = "O%d%s%d" % (values["type"], values["CTC"], voc_size)
            else:
                raise "Layer %s not defined." % layer_name
            model_str.append(layer_str)
        if self.model[-1]["name"] != "output":
            values = read_layer_default("output")
            print(values["type"], values["CTC"], voc_size)
            layer_str = "O%d%s%d" % (values["type"], values["CTC"], voc_size)
            model_str.append(layer_str)
        return '--net_spec \'[' + ' '.join(model_str) + ']\''


# model = read_json('engines/schemas/sample.json')
# translator = ModelTranslator(model, 'kraken')
# print(translator.model_str)



















