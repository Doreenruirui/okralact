import json
from jsonschema import Draft4Validator, RefResolver
import os


class Config(object):
    def __init__(self, configs):
        for attr in configs:
            setattr(self, attr, configs[attr])


def read_json(json_file):
    with open(json_file) as f_:
        data = json.loads(f_.read())
    return data


def write_json(dict_res, json_file):
    with open(json_file, 'w') as f_:
        json.dump(dict_res, f_)


def validate(schema, config):
    resolver = RefResolver('file://%s/engines/schemas/' % os.getcwd(), None)
    validator = Draft4Validator(schema, resolver=resolver)
    error_message = []
    for eno, error in enumerate(validator.iter_errors(config)):
        if len(error.path) > 0:
            error_message.append('error %d:\tparameter %s, %s' %(eno,  error.path[0], error.message))
        else:
            error_message.append('error %d:\t%s' % (eno, error.message))
    return error_message


def validate_file(config_file):
    common_schema = read_json('engines/schemas/common.schema')
    config = read_json(config_file)
    errors = validate(common_schema, config)
    if len(errors) > 0:
        return errors
    else:
        engine = config["engine"]
        # print('engines/schemas/%s.schema' % engine)
        engine_schema = read_json('engines/schemas/%s.schema' % engine)
        errors = validate(engine_schema, config)
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


def load_jsonref(ref_path):
    ref_file, ref_propty, ref_attr = ref_path.split('/')
    ref_file = ref_file[:-1]
    schema_path = '%s/engines/schemas/%s' % (os.getcwd(), ref_file)
    print(schema_path)
    ref_schema = read_json(schema_path)
    return ref_schema[ref_propty][ref_attr]


def read_help_information_html(engine):
    schema = read_json('engines/schemas/%s.schema' % engine)
    attrs = schema['properties']
    help_info = []
    for k in attrs:
        print(k, attrs[k])
        if "$ref" in attrs[k]:
            ref_path = attrs[k]["$ref"]
            cur_node = load_jsonref(ref_path)
        else:
            cur_node = attrs[k]
        help_info.append([k, str(cur_node["default"]), cur_node["description"]])
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


# print(validate_file("engines/schemas/sample.json"))
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
