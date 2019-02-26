from flask import Flask, render_template, redirect, url_for, request, flash, send_file
from flask_uploads import UploadSet, configure_uploads, ARCHIVES, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename
from app import app
import os,shutil
import time, hashlib
from app.lib.process_file import rename_file
from rq import get_current_job
from rq.job import Job
import tarfile
import shutil


import os, sys
parentdir = os.getcwd().rsplit('/', 1)[0]
print(parentdir)
sys.path.insert(0, parentdir)
import engines


class UploadForm(FlaskForm):
    archive = FileField(validators=[FileAllowed(set(['tar.gz'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


def get_files():
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return files_list


def get_file_status(file_list):
    dict_status = {}
    for fn in file_list:
        if fn in app.job_file2id:
            job_id = app.job_file2id[fn]
            job = Job.fetch(job_id, app.redis)
            dict_status[fn] = job.status
        else:
            prefix = fn.rsplit('.', 2)[0]
            print(prefix)
            print(os.path.join(os.getcwd(), 'engines/model', prefix))
            if os.path.exists(os.path.join('engines/model', prefix)):
                dict_status[fn] = "finished"
            else:
                dict_status[fn] = "no"
    return dict_status


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    f = form.archive.data
    if form.validate_on_submit():
        filename = secure_filename(f.filename)
        files_list = os.listdir(app.config['UPLOAD_FOLDER'])
        filename = rename_file(filename, files_list)
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        success = True
    else:
        success = False
    return render_template('index.html', success=success, form=form)


#Manage Files
@app.route('/files')
def manage_file():
    # print(app.config)
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('files.html', files_list=files_list)


@app.route('/delete/<filename>')
def delete_file(filename):
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
    return redirect(url_for('manage_file'))


#Manage jobs
@app.route('/jobs')
def manage_job():
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    dict_status = get_file_status(files_list)
    print(app.job_file2id)
    print(dict_status)
    return render_template('jobs.html', files_list=files_list, dict_status=dict_status)


#Run jobs
@app.route('/run/<filename>')
def train_model(filename):
    if filename not in app.job_file2id:
        job = app.task_queue.enqueue('train.train_from_file', '../static/data/%s' % filename)
        job_id = job.get_id()
        app.job_file2id[filename] = job_id
        app.job_id2file[job_id] = filename
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    dict_status = get_file_status(files_list)
    return render_template('jobs.html', files_list=files_list, dict_status=dict_status)


#download models
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


