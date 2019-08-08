import tarfile
import os
from os.path import join as pjoin
import subprocess
import random
import numpy as np
from shutil import rmtree
import json


def read_json(json_file):
    with open(json_file) as f_:
        data = json.loads(f_.read())
    return data


def write_json(dict_res, json_file):
    with open(json_file, 'w') as f_:
        json.dump(dict_res, f_)


def extract_file(filename, foldername):
    with tarfile.open(filename, 'r:gz') as _tar:
        for tarinfo in _tar:
            if tarinfo.isdir():
                continue
            fn = tarinfo.name.split('/')[1]
            if fn.startswith('.'):
                continue
            if fn.endswith('.png') or tarinfo.name.endswith('.txt'):
                tarinfo.name = fn
                _tar.extract(tarinfo, foldername)


def clear_data(foldername):
    if os.path.exists(foldername):
        rmtree(foldername)
    os.makedirs(foldername)


def split_train_test(data_folder, tmp_folder, train_ratio=0.9, engine='kraken'):
    files = []
    for fn in os.listdir(data_folder):
        if fn.endswith('.png'):
            prefix = fn.split('.')[0]
            if os.path.exists(pjoin(data_folder, prefix + '.gt.txt')):
                files.append(prefix)
    random.shuffle(files)

    nfile = len(files)
    ntrain = int(np.floor(nfile * train_ratio))
    ntest = nfile - ntrain
    train_files = files[:ntrain]
    eval_files = files[ntrain:]
    if ntest == 0 and engine == 'kraken':
        ntest = int(np.ceil(nfile * 0.1))
        eval_files = files[:nfile][-ntest:]

    if engine == 'tesseract':
        postfix = '.lstmf'
    else:
        postfix = '.png'

    if len(train_files) > 0:
        with open(pjoin(tmp_folder, 'list.train'), 'w') as f_:
            for fn in train_files:
                f_.write(pjoin(data_folder, fn + postfix) + '\n')
    if len(eval_files) > 0:
        with open(pjoin(tmp_folder, 'list.eval'), 'w') as f_:
            for fn in eval_files:
                f_.write(pjoin(data_folder, fn + postfix) + '\n')
    return ntrain, ntest


def load_jsonref(ref_path):
    ref_file, ref_propty, ref_attr = ref_path.rsplit('/', 2)
    ref_file = ref_file[:-1]
    schema_path = '%s/engines/schemas/%s' % (os.getcwd(), ref_file)
    print(schema_path)
    ref_schema = read_json(schema_path)
    return ref_schema[ref_propty][ref_attr]


def read_layer_info(layername):
    layer_schema = read_json("engines/schemas/models/layer_%s.schema" % layername)
    default_values = {}
    for key in layer_schema["definitions"]:
        default_values[key] = layer_schema["definitions"][key]["default"]
    return default_values


def read_model_info(engine):
    engine_schema = read_json('engines/schemas/models/model_%s.schema' % engine)
    model = engine_schema["definitions"]["model"]
    layers = model["items"]["oneOf"]
    model["layers"] = []
    help_info = []
    help_info.append("model", model["type"], '', model["description"])
    for layer in layers:
        layer_def = load_jsonref('models/' + layer["$ref"])
        for para in layer_def["properties"]:
            para_def = load_jsonref("models/" + layer_def["properties"][para]["$ref"])
            print(para_def)
            layer_def["properties"][para] = para_def
            model["layers"].append(layer_def)

    return model


def read_help_information_html(engine):
    schema = read_json('engines/schemas/engine_%s.schema' % engine)
    attrs = schema['properties']
    help_info = []
    for k in attrs:
        print(k, attrs[k])
        if k == "model":
            read_model_info(engine)
            continue
        elif "$ref" in attrs[k]:
            ref_path = attrs[k]["$ref"]
            cur_node = load_jsonref(ref_path)
        elif attrs[k]["type"] == "object":
            continue
        else:
            cur_node = attrs[k]
        if cur_node["type"] == "number":
            help_info.append([k, cur_node["format"], str(cur_node["default"]), cur_node["description"]])
        else:
            if "enum" in cur_node:
                help_info.append([k, cur_node["type"], str(cur_node["default"]), "Allowed Value: " + ', '.join(cur_node["enum"]) + '. ' + cur_node["description"]])
            else:
                help_info.append([k, cur_node["type"], str(cur_node["default"]), cur_node["description"]])
    return help_info


read_help_information_html("kraken")

