from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from lib.file_operation import get_engines


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


class UploadModelForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['tar.gz'])), FileRequired(u'Choose a file!')])
    select_config = SelectField(u'config')
    submit = SubmitField(u'upload')


class SelectConfigForm(FlaskForm):
    select_config = SelectField(u'config')
    select_data = SelectField(u'data')
    submit = SubmitField(u'run')
    submit_valid = SubmitField(u'valid')


class SelectEngineForm(FlaskForm):
    engine_choices = get_options(get_engines())
    select_engine = SelectField(u'engine', choices=engine_choices)
    submit = SubmitField(u'show')


class SelectEvalForm(FlaskForm):
    select_test = SelectField(u'test', id='select_test')
    select_model = SelectField(u'model', id='select_model')
    submit = SubmitField(u'evaluate')
