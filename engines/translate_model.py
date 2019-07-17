import json
from engines.validate_parameters import read_json


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
        self.model_str = self.translate()

    def translate(self):
        method = getattr(self, self.engine, lambda: "Invalid Engine")
        return method()

    def kraken(self):
        model_str = []
        for layer in self.model["layers"]:
            layer_name = layer["name"]
            values = read_layer_default(layer_name)                        # Get default value for each layer attribute
            values = {k: layer[k] if k in layer else values[k] for k in values} # Rewrite value according to user specific configuration
            if layer_name == "cnn":
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
                                                 values["b"],
                                                 values["dim_e"],
                                                 values["dim_f"])
            elif layer_name == "pooling":
                layer_str = 'MP%d,%d,%d,%d' % (values["height"],
                                               values["width"],
                                               values["y_stride"],
                                               values["x_stride"])
            elif layer_name == "dropout":
                layer_str = "Do%.2f,%d" % (values["prob"], values["dim"])
            elif layer_name == "output":
                layer_str = "o%d%s%d" % (values["type"], values["CTC"], values["size"])
            else:
                raise "Layer %s not defined." % layer_name
            model_str.append(layer_str)
        return '--spec [' + ' '.join(model_str) + ']'

    def ocropus(self):      # ocoropus only allow user specific rnn layer
        if len(self.model["layers"]) > 0:
            rnn_layer = self.model["layers"][0]["rnn"]
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

    def calamari(self):
        model_str = []
        for layer in self.model["layers"]:
            layer_name = layer["name"]
            values = read_layer_default(layer_name)  # Get default value for each layer attribute
            values = {k: layer[k] if k in layer else values[k] for k in
                      values}  # Rewrite value according to user specific configuration
            if layer_name == "cnn":
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
        return '--network=%s' % (','.join(model_str))

    def tesseract(self):
        model_str = []
        for layer in self.model["layers"]:
            layer_name = layer["name"]
            values = read_layer_default(layer_name)  # Get default value for each layer attribute
            values = {k: layer[k] if k in layer else values[k] for k in
                      values}  # Rewrite value according to user specific configuration
            if layer_name == "cnn":
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
                layer_str = 'MP%d,%d' % (values["height"], values["width"])
            elif layer_name == "output":
                layer_str = "o%d%s%d" % (values["type"], values["CTC"], values["size"])
            else:
                raise "Layer %s not defined." % layer_name
            model_str.append(layer_str)
        return '--net_spec [' + ' '.join(model_str) + ']'


model = read_json('engines/schemas/sample.json')
translator = ModelTranslator(model, 'tesseract')
translator.kraken()
print(translator.model_str)



















