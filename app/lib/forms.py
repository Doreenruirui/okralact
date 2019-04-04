from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from lib.file_operation import get_files, get_configs, get_engines


def get_options(file_list):
    nconfig = len(file_list)
    choices = []
    for i in range(nconfig):
        choices.append((str(i), file_list[i]))
    return choices


class UploadDataForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['tar.gz'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


class UploadConfigForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['json'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


class SelectConfigForm(FlaskForm):
    config_choices = get_options(get_configs())
    select_config = SelectField(u'config', choices=config_choices)
    data_choices = get_options(get_files())
    select_data = SelectField(u'data', choices=data_choices)
    submit = SubmitField(u'run')


class SelectEngineForm(FlaskForm):
    engine_choices = get_options(get_engines())
    select_engine = SelectField(u'engine', choices=engine_choices)
    submit = SubmitField(u'show')
