import os


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or '85629d74c5332853c107cc43417169bd14daa36f352620b2'
    UPLOAD_FOLDER = os.getcwd() + '/static/data'
    CONFIG_FOLDER = os.getcwd() + '/static/configs'
    MODEL_FOLDER = os.getcwd() + '/static/model'
    TMP_FOLDER = os.getcwd() + '/static/tmp'

