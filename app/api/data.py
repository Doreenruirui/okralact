from app.api import bp
from lib.file_operation import get_files


@bp.route('/dataset', methods=['GET'])
def get_dataset():
    files = get_files()
    dict_files = {'files': files}


@bp.route('/config', methods=['GET'])
def get_configs():
    pass

