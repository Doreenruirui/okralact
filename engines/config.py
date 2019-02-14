import json


class Config(object):
    def __init__(self, config_file):
        with open(config_file) as f:
            data = json.load(f)
        for attr in data:
            setattr(self, attr, data[attr])


# config = Config('./data/config.txt')
# print(config.model_dir)

