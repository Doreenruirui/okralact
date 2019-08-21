import json
from jsonschema import Draft4Validator, RefResolver
import os
from engines.common import read_json
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
    for eno, error in enumerate(validator.iter_errors(config)):
        if len(error.path) > 0:
            error_message.append('parameter %s, %s' % (error.path[0], error.message))
        else:
            error_message.append('%s' % error.message)
    return error_message


def validate_model(model, engine):
    err_str = []
    layers = read_json('engines/schemas/models/layer_all_%s.schema' % engine)["definitions"]
    for ele in model:
        for key in ele:
            if key not in layers:
                err_str.append('parameter model, layer %s is not defined in the model of engine %s' % (key, engine))
            else:
                resolver = RefResolver('file://%s/engines/schemas/models/' % os.getcwd(), None)
                validator = Draft4Validator(layers[key], resolver=resolver)
                for eno, error in enumerate(validator.iter_errors(ele)):
                    if len(error.path) > 0:
                        err_str.append('parameter model, layer %s, %s' % (key, error.message))
                    else:
                        err_str.append('parameter model, layer %s, %s' % (key, error.message))
    return err_str

def validate_path(continue_from, new_config):
    err_str = []
    model_dir =  get_model_dir(continue_from["trainset"], continue_from["config"])

    if not os.path.exists(os.path.join(model_root,  model_dir, continue_from["model"])):
        err_str.append('parameter continue_from, model %s does not exist')
    old_config = read_json(os.path.join(config_root,  continue_from["config"]))
    if old_config["engine"] != new_config["engine"]:
        err_str.append('parameter engine, engines for old model and new model not match')
    return err_str


def validate_file(config_file):
    common_schema = read_json('engines/schemas/common.schema')
    config = read_json(config_file)
    errors = validate(common_schema, config)
    print(errors)
    if len(errors) > 0:
        return errors
    else:
        engine = config["engine"]
        # print('engines/schemas/%s.schema' % engine)
        engine_schema = read_json('engines/schemas/engine_%s.schema' % engine)
        errors_model = []
        if "continue_from" in config:
            continue_from = config["continue_from"]
            del config["continue_from"]
            errors_continue = validate_path(continue_from, config)
        errors +=  errors_continue
        if "model" in config:
            model = config["model"]
            del config["model"]
            errors_model = validate_model(model, engine)
        errors += validate(engine_schema, config)
        errors += errors_model
        nerr = len(errors)
        for i in range(nerr):
            errors[i] = 'Error %d: %s' % (i, errors[i])
        return errors


def validate_string(config_str):
    common_schema = read_json('engines/schemas/common.schema')
    config = json.loads(config_str)
    errors = validate(common_schema, config)
    if len(errors) > 0:
        return errors
    else:
        engine = config["engine"]
        engine_schema = read_json('engines/schemas/%s.schema' % engine)
        errors = validate(engine_schema, config)
        return errors


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




# print(validate_file("static/configs/sample_kraken_continue.json"))
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
