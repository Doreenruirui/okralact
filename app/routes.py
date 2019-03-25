from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_uploads import UploadSet, configure_uploads, ARCHIVES, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField, SelectField
from werkzeug.utils import secure_filename
from app import app
import os,shutil
import time, hashlib
from app.lib.process_file import rename_file
from rq import get_current_job
from rq.job import Job
import tarfile
import shutil
import os
import sys

parentdir = os.getcwd().rsplit('/', 1)[0]
print(parentdir)
sys.path.insert(0, parentdir)


def get_files():
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return files_list


def get_configs():
    configs_list = os.listdir(app.config['CONFIG_FOLDER'])
    return configs_list


def get_options(file_list):
    nconfig = len(file_list)
    choices = []
    for i in range(nconfig):
        choices.append((str(i), file_list[i]))
    return choices


def get_file_status():
    dict_status = {}
    for job_id in app.job_id2file:
        job = Job.fetch(job_id, app.redis)
        filename, config = app.job_id2file[job_id]
        dict_status[(filename, config)] = job.status
    return dict_status


class UploadDataForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['tar.gz'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


class UploadConfigForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['txt'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


class SelectConfigForm(FlaskForm):
    config_choices = get_options(get_configs())
    select_config = SelectField(u'config', choices=config_choices)
    data_choices = get_options(get_files())
    select_data = SelectField(u'data', choices=data_choices)
    submit = SubmitField(u'run')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadDataForm()
    f = form.archive.data
    FILE_CHOICES = [('1', 'configuration'), ('2', 'dataset')]
    if form.validate_on_submit():
        filename = secure_filename(f.filename)
        files_list = get_files()
        filename = rename_file(filename, files_list)
        file_type = dict(FILE_CHOICES).get(form.select.data)
        # print(file_type)
        if file_type == 'configuration':
            f.save(os.path.join(app.config['CONFIG_FOLDER'], filename))
        else:
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        success = True
    else:
        success = False
    return render_template('index.html', success=success, form=form)


# Manage Files
@app.route('/data', methods=['GET', 'POST'])
def manage_data():
    files_list = get_files()
    form = UploadDataForm()
    f = form.archive.data
    if form.validate_on_submit():
        filename = secure_filename(f.filename)
        prefix = '.'.join(filename.rsplit('.', 2)[:-2])
        filename = rename_file(prefix, '.tar.gz', files_list)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('manage_data'))
    return render_template('data.html', form=form, files_list=files_list)


# Manage Files
@app.route('/configs', methods=['GET', 'POST'])
def manage_configs():
    configs_list = get_configs()
    form = UploadConfigForm()
    f = form.archive.data
    if form.validate_on_submit():
        filename = secure_filename(f.filename)
        prefix = filename.rsplit('.')[0]
        filename = rename_file(prefix, '.txt', configs_list)
        f.save(os.path.join(app.config['CONFIG_FOLDER'], filename))
        return redirect(url_for('manage_configs'))
    return render_template('data.html', form=form, files_list=configs_list)


@app.route('/delete/<filename>')
def delete_data(filename):
    if filename in app.job_file2id:
        app.job_file2id.pop(filename, None)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.remove(file_path)
    prefix = filename.rsplit('.', 2)[0]
    model_file = os.path.join(os.getcwd(), 'engines/model', 'model_%s' % filename)
    if os.path.exists(model_file):
        os.remove(model_file)
    model_folder = os.path.join(os.getcwd(), 'engines/model', prefix)
    if os.path.exists(model_folder):
        shutil.rmtree(model_folder, ignore_errors=True)
    return redirect(url_for('manage_data'))


@app.route('/delete/<filename>')
def delete_config(filename):
    if filename in app.job_file2id:
        app.job_file2id.pop(filename, None)
    file_path = os.path.join(app.config['CONFIG_FOLDER'], filename)
    os.remove(file_path)
    return redirect(url_for('manage_configs'))


# Manage jobs
@app.route('/jobs', methods=['GET', 'POST'])
def manage_job():
    files_list = get_files()
    dict_status = get_file_status()
    print(app.job_file2id)
    print(dict_status)
    form = SelectConfigForm()
    if request.method == 'POST':
        data_choices = dict(get_options(get_files()))
        config_choices = dict(get_options(get_configs()))
        select_config = config_choices.get(form.select_config.data)
        select_data = data_choices.get(form.select_data.data)
    #     redirect(url_for('manage_job'))
        print('data', select_data)
        print('config:', select_config)
        return redirect(url_for('train_model', filename=select_data, config=select_config))
    return render_template('jobs.html', form=form, dict_status=dict_status)


# Run jobs
@app.route('/run', methods=['POST', 'GET'])
def train_model():
    print('train_model')
    filename = request.args.get('filename', None)
    config = request.args.get('config', None)
    print(filename, config)
    # form = SelectConfigForm()
    if (filename, config) not in app.job_file2id:
        job = app.task_queue.enqueue('train.train_from_file', '../static/data/%s' % filename)
        job_id = job.get_id()
        app.job_file2id[(filename, config)] = job_id
        app.job_id2file[job_id] = (filename, config)
    print(app.job_id2file)
    # files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return redirect(url_for('manage_job'))


# download models
@app.route('/download/<filename>')
def download(filename):
    prefix = filename.rsplit('.', 2)[0]
    model_dir = os.path.join(os.getcwd(), 'engines/model/')
    model_files = os.listdir(os.path.join(model_dir, prefix))
    outfile = os.path.join(model_dir, 'model_%s.tar.gz' % prefix)
    if os.path.exists(outfile):
        os.remove(outfile)
    with tarfile.open(outfile, "w:gz") as _tar:
        for fn in model_files:
            new_fn = os.path.join(model_dir, prefix, fn)
            _tar.addfile(tarfile.TarInfo('model/%s' % fn), open(new_fn))
    return send_file(outfile, mimetype='text/tar', attachment_filename='model.tar.gz', as_attachment=True)


# Manual of Using OCR Engines
@app.route('/manual')
def manual():
    return render_template('manual.html')

