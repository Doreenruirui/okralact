import json
from jsonschema import Draft4Validator, RefResolver
import os
from lib.file_operation import read_json, read_config_str
from engines import model_root, config_root
from lib.file_operation import get_model_dir


class Config(object):
    def __init__(self, configs):
        for attr in configs:
            setattr(self, attr, configs[attr])


def validate(schema, config):
    resolver = RefResolver('file://%s/engines/schemas/' % os.getcwd(), None)
    validator = Draft4Validator(schema, resolver=resolver)
    error_message = []
    for error in validator.iter_errors(config):
        if len(error.path) > 0:
            error_message.append('parameter %s, %s' % (error.path[0], error.message))
        else:
            error_message.append('%s' % error.message)
    return error_message


def validate_model(model, engine):
    err_str = []
    if type(model) is not list:
        err_str.append('parameter model, model should be a list of arrays')
        return err_str
    layers = read_json('engines/schemas/models/layer_all_%s.schema' % engine)["definitions"]
    layer_no = 0
    for ele in model:
        if type(ele) is not dict:
            err_str.append('parameter model, layer %d must be a dictionary' % layer_no)
            continue
        if len(ele.keys()) != 1:
            err_str.append('parameter model, layer %d must only contains one layer'  % layer_no)
            continue
        for key in ele:
            if key not in layers:
                err_str.append('parameter model, layer %s is not defined in the model of engine %s' % (key, engine))
            else:
                resolver = RefResolver('file://%s/engines/schemas/models/' % os.getcwd(), None)
                validator = Draft4Validator(layers[key], resolver=resolver)
                for error in validator.iter_errors(ele):
                    err_str.append('parameter model, layer %s, %s' % (key, error.message))
        layer_no += 1
    return err_str


def validate_continue_from(continue_from_schema, new_config):
    err_str = []
    engine = new_config["engine"]
    # check whether continue from parameter is valid against the engine schema
    resolver = RefResolver('file://%s/engines/schemas/' % os.getcwd(), None)
    validator = Draft4Validator(continue_from_schema, resolver=resolver)
    continue_from = new_config["continue_from"]
    for error in validator.iter_errors(continue_from):
        err_str.append('parameter continue_from, %s' % error.message)
    if len(err_str) > 0:
        return err_str
    # check whether engine matches
    old_config = read_json(os.path.join(config_root,  continue_from["config"]))
    if old_config["engine"] != new_config["engine"]:
        err_str.append('parameter engine, engines for old model and new model not match')
        return err_str
    # check whether the path to continue from exists
    model_dir =  get_model_dir(continue_from["trainset"], continue_from["config"])
    if engine == 'tesseract':
        model_path = os.path.join(model_root,  model_dir, 'checkpoint', continue_from["model"])
    else:
        model_path = os.path.join(model_root,  model_dir, continue_from["model"])
    if engine == 'calamari':
        model_path += '.json'
    if not os.path.exists(model_path):
        err_str.append('parameter continue_from, model does not exist')
    # check whether the model structure is right
    if "model" in new_config:
        if engine  == 'calamari':
            if new_config['model'] != old_config["model"]:
                err_str.append('parameter model, old model and new model must match for calamari.')
                return err_str
        elif engine == 'ocropus':
            err_str.append('parameters model, ocropus does not support new model structure for fine tuning.')
            return err_str
        append_index = new_config["append"]
        if "append" not in new_config or append_index < 1:
            err_str.append('parameter append, please assign a valid append')
        new_model = new_config["model"]
        old_model = old_config["model"]
        len_old_model = len(old_model) if "input" in old_model[0] else len(old_model) + 1
        len_old_model = len_old_model - 1 if "output" in old_model[-1] else len_old_model
        if append_index >= len_old_model:
            err_str.append('parameter append, append_index must be less than the number of layers (excluding output layer, including input layer).')
        concat_model = old_model[:append_index] if "input" in old_model[0] else old_model[:append_index - 1]
        concat_model += new_model
    else:
        if "append" in new_config:
            err_str.append('parameter append, please specify the model structure to append.')
        if engine == 'calamari':
            if "model" in old_config:
                err_str.append('parameter model, old model and new model must match for calamari')
    return err_str


def validate_string(config_str):
    config, err = read_config_str(config_str)  # read configuration file
    if len(err) >  0:
        errors = ['Configuration file is not valid dictionary.']
        for e  in err:
            errors.append('\t' + e)
        return errors
    common_schema = read_json('engines/schemas/common.schema')  # valid against common schema
    errors = validate(common_schema, config)
    if len(errors) > 0:
        return errors
    errors =  []
    engine = config["engine"]
    engine_schema = read_json('engines/schemas/engine_%s.schema' % engine)
    errors_model = []
    if "model" in config:                                       # valid against model schema
        model = config["model"]
        errors_model = validate_model(model, engine)
    errors += errors_model
    if "continue_from" in config:                               # valid whether the continue from path exists
        errors += validate_continue_from(engine_schema["properties"]["continue_from"], config)
        del config["continue_from"]
    elif "append"  in config:
        errors += ['parameter append, please specify the model structure to append.']
    #     errors +=  errors_continue
    if "model" in config:
        del config["model"]
    errors += validate(engine_schema, config)                   # valid against engine schema
    nerr = len(errors)
    for i in range(nerr):
        errors[i] = 'Error %d: %s' % (i, errors[i])
    return  errors


def validate_file(config_file):
    with open(config_file) as f_:
        content = f_.read()
    errors = validate_string(content)
    print(errors)


def read_parameter_from_schema(schema):
    attrs = schema['properties']
    configs = {}
    for k in attrs:
        configs[k] = attrs[k]["default"]
    return configs


def read_help_information(engine):
    schema = read_json('schemas/%s.schema' % engine)
    attrs = schema['properties']
    help_info = 'OCR Engine: %s\n' % engine
    help_info += 'Parameters: \n'
    for k in attrs:
        help_info += '\t --%s\tdefault:[%s]\t%s\n' % (k, str(attrs[k]["default"]), attrs[k]["description"])
    return help_info


def read_parameters(config_file):
    configs = read_json(config_file)
    engine = configs["engine"]
    schema = read_json('engines/schemas/%s.schema' % engine)
    new_configs = read_parameter_from_schema(schema)
    for attr in new_configs:
        if attr in configs:
            new_configs[attr] = configs[attr]
    # updated_configs = Config(new_configs)
    return new_configs




# print(validate_file("static/configs/sample_kraken_valid.json"))
# read_parameters('engines/schemas/sample.json')
# print(read_help_information('calamari'))
# errors = valiadte_file('engines/schemas/sample.json')
# for error in errors:
#     print(error)
# import validate
# with open("./schemas/calamari.schema") as f_:
#     schema_data = f_.read()
# schema = json.loads(schema_data)
#
# with open("schemas/sample.json") as f_:
#     sample_data = f_.read()
# sample = json.loads(sample_data)
# validate(sample, schema)
# v = Draft4Validator(schema)
# errors = []
#
