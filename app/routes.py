from flask import Flask, render_template, redirect, url_for, request, flash
from flask_uploads import UploadSet, configure_uploads, ARCHIVES, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField
from werkzeug.utils import secure_filename
from app import app
import os,shutil
import time, hashlib
import tarfile
from app.lib.process_file import rename_file

job_id = None


class UploadForm(FlaskForm):
    archive = FileField( validators=[FileAllowed(set(['tar.gz'])), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'upload')


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
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.remove(file_path)
    return redirect(url_for('manage_file'))


#Manage jobs
@app.route('/jobs')
def manage_job():
    global job_id
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('jobs.html', files_list=files_list, job_id=job_id)


#Run jobs
@app.route('/run/<filename>')
def train_model(filename):
    global job_id
    job_id = filename
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('jobs.html', files_list=files_list, job_id=job_id)


#Stop Jobs
@app.route('/stop/<filename>')
def stop_train(filename):
    global job_id
    job_id = None
    files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    # return redirect(url_for('manage_job', files_list=files_list, job_id=job_id))
    return render_template('jobs.html', files_list=files_list, job_id=job_id)

