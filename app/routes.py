from flask import render_template, redirect, url_for, request, send_file
from werkzeug.utils import secure_filename
from app import app
from lib.file_operation import rename_file
from rq.job import Job
import tarfile
import shutil
import os
import sys
from engines.validate_parameters import valiadte_string
import engines
import json
import base64
from lib.file_operation import list_model_dir, get_engines, get_configs, get_files
from app.lib.forms import SelectEngineForm, UploadConfigForm, UploadDataForm, SelectConfigForm, SelectModelForm, get_options
from engines.validate_parameters import read_help_information_html


# parentdir = os.getcwd().rsplit('/', 1)[0]
# print(parentdir)
# sys.path.insert(0, parentdir)


def get_file_status():
    dict_status = {}
    for job_id in app.job_id2file:
        job = Job.fetch(job_id, app.redis)
        filename, config = app.job_id2file[job_id]
        dict_status[(filename, config)] = job.status
    return dict_status

def get_eval_status():
    dict_status = {}
    for job_id in app.eval_id2file:
        job = Job.fetch(job_id, app.redis)
        trainname,testname, config = app.eval_id2file[job_id]
        dict_status[(trainname,testname, config)] = job.status
    return dict_status

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
@app.route('/configs', methods=['GET', 'POST'], defaults={'error_message': ''})
@app.route('/configs/<error_message>', methods=['GET', 'POST'])
def manage_configs(error_message):
    configs_list = get_configs()
    form = UploadConfigForm()
    f = form.archive.data
    errors = error_message.split('\n')
    print(errors)
    print(error_message)
    if form.validate_on_submit():
        content = f.read()
        errors = valiadte_string(content)
        print(errors)
        if len(errors) > 0:
            print('print_error')
            return redirect(url_for('manage_configs', error_message='\n'.join(errors)))
        else:
            filename = secure_filename(f.filename)
            prefix = filename.rsplit('.')[0]
            filename = rename_file(prefix, '.json', configs_list)
            with open(os.path.join(app.config['CONFIG_FOLDER'], filename), 'w', encoding='utf-8') as f_:
                json.dump(json.loads(content.decode('ascii')), f_)
            return redirect(url_for('manage_configs'))
    return render_template('configs.html', errors=errors, form=form, files_list=configs_list)


@app.route('/delete_data/<filename>')
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


@app.route('/delete_config/<filename>')
def delete_config(filename):
    if filename in app.job_file2id:
        app.job_file2id.pop(filename, None)
    file_path = os.path.join(app.config['CONFIG_FOLDER'], filename)
    os.remove(file_path)
    return redirect(url_for('manage_configs'))


# Manage jobs
@app.route('/jobs', methods=['GET', 'POST'])
def manage_job():
    dict_status = get_file_status()
    print(app.job_file2id)
    print(dict_status)
    form = SelectConfigForm()
    if request.method == 'POST':
        data_choices = dict(get_options(get_files()))
        config_choices = dict(get_options(get_configs()))
        print(get_configs())
        select_config = config_choices.get(form.select_config.data)
        select_data = data_choices.get(form.select_data.data)
    #     redirect(url_for('manage_job'))
        print('data', select_data)
        print('config:', select_config)
        return redirect(url_for('train_model', filename=select_data, config=select_config))
    return render_template('jobs.html', form=form, dict_status=dict_status)



# Manage Models
@app.route('/models', methods=['GET', 'POST'])
def manage_model():
    model_dict = list_model_dir()
    for ele in model_dict:
        if not os.listdir(os.path.join(os.getcwd(), 'static/model', model_dict[ele])):
            del model_dict[ele]
    print(model_dict)
    return render_template('models.html', dict_model=model_dict)

# Manage Evals
@app.route('/evaluation', methods=['GET', 'POST'])
def manage_eval():
    dict_status = get_eval_status()
    print(app.eval_file2id)
    print(dict_status)
    form = SelectModelForm()
    if request.method == 'POST':
        train_choices = dict(get_options(get_files()))
        test_choices = dict(get_options(get_files()))
        config_choices = dict(get_options(get_configs()))
        print(get_configs())
        select_config = config_choices.get(form.select_config.data)
        select_test = train_choices.get(form.select_test.data)
        select_train = test_choices.get(form.select_train.data)
    #     redirect(url_for('manage_job'))
        print('train', select_train)
        print('test', select_test)
        print('config:', select_config)
        return redirect(url_for('eval_model', testname=select_test, trainname=select_train, config=select_config))
    return render_template('eval.html', form=form, dict_status=dict_status)


# Run jobs
@app.route('/run', methods=['POST', 'GET'])
def train_model():
    print('train_model')
    filename = request.args.get('filename', None)
    config = request.args.get('config', None)
    print(filename, config)
    # form = SelectConfigForm()
    if (filename, config) not in app.job_file2id:
        job = app.task_queue.enqueue('engines.train.train_from_file', filename, config)
        job_id = job.get_id()
        app.job_file2id[(filename, config)] = job_id
        app.job_id2file[job_id] = (filename, config)
    print(app.job_id2file)
    # files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return redirect(url_for('manage_job'))

# Run jobs
@app.route('/eval', methods=['POST', 'GET'])
def eval_model():
    print('train_model')
    trainname = request.args.get('trainname', None)
    testname = request.args.get('testname', None)
    config = request.args.get('config', None)
    print(trainname, testname, config)
    if (trainname,  testname, config) not in app.eval_file2id:
        job = app.task_queue.enqueue('engines.train.eval_from_file', trainname,  testname, config)
        job_id = job.get_id()
        app.eval_file2id[(trainname, testname, config)] = job_id
        app.eval_id2file[job_id] = (trainname,  testname, config)
    print(app.eval_id2file)
    return redirect(url_for('manage_eval'))

def tardir(path, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))


# download model
@app.route('/download/<filename>', methods=['GET', 'POST'])
def download(filename):
    root_dir = os.getcwd()
    model_dir = 'static/model/'
    # model_files = os.listdir(os.path.join(model_dir, filename))
    # print(model_files)
    outfile = os.path.join(root_dir, model_dir, 'model_%s.tar.gz' % filename)
    if os.path.exists(outfile):
        os.remove(outfile)
    tardir(os.path.join(root_dir, model_dir, filename), outfile)
    # with tarfile.open(outfile, "w:gz") as _tar:
    #     for fn in model_files:
    #         new_fn = os.path.join(model_dir, filename, fn)
    #         print(new_fn)
    #         _tar.add('model/%s' % fn, new_fn)
    #         # _tar.add(tarfile.TarInfo('model/%s' % fn), open(new_fn))
    return send_file(outfile, mimetype='text/tar', attachment_filename='model.tar.gz', as_attachment=True)


# Manual of Using OCR Engines
@app.route('/', methods=['GET', 'POST'], defaults={'engine': 'kraken'})
@app.route('/<engine>',  methods=['GET', 'POST'])
def manual(engine):
    # Manage jobs
    print(engine)
    help_info = read_help_information_html(engine)
    form = SelectEngineForm()
    if request.method == 'POST':
        engine_choices = dict(get_options(get_engines()))
        select_engine = engine_choices.get(form.select_engine.data)
        #     redirect(url_for('manage_job'))
        print('engine', select_engine)
        return redirect(url_for('manual', engine=select_engine))
    return render_template('manual.html', form=form, engine=engine, help_info=help_info)

