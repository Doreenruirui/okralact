from flask import render_template, redirect, url_for, request, send_file
from werkzeug.utils import secure_filename
from app import app, model_root, config_root, eval_root
from lib.file_operation import get_files, get_configs, get_models, read_json, compress_file,  extract_file, rename_file, add_model, get_model_dir, list_model_dir, read_list, update_list,del_model_dir
from rq.job import Job
import tarfile
import os
from engines.validate_parameters import validate_string
import json
from app.lib.forms import *
from engines.common import read_help_information_html, read_model_param
from app.modup import publish_model


def get_file_status():
    dict_status = {}
    for job_id in app.job_id2file:
        filename, config = app.job_id2file[job_id]
        try:
            job = Job.fetch(job_id, app.redis)
            dict_status[(filename, config)] = job.get_status()
        except:
            dict_status[(filename,  config)] = 'finished'
    return dict_status


def get_valid_status():
    dict_status = {}
    for job_id in app.valid_id2file:
        filename, config = app.valid_id2file[job_id]
        try:
            job = Job.fetch(job_id, app.redis)
            dict_status[(filename, config)] = job.get_status()
        except:
            dict_status[(filename,  config)] = 'finished'
    return dict_status


def get_model_list(model_dir):
    tess_path = os.path.join(model_root, model_dir, "checkpoint")
    if os.path.exists(tess_path) and os.path.isdir(tess_path):
        models = [ele for ele in os.listdir(tess_path)]
    else:
        models = [ele for ele in os.listdir(os.path.join(model_root, model_dir))]
    print("models:\n", models)
    file_list = []
    prefix_camalari = {}
    for ele in models:
        if ele.endswith('mlmodel') or ele.endswith('.pyrnn.gz') or ele.endswith("checkpoint"):
            file_list.append(ele)
        elif ".ckpt." in ele and ele != "checkpoint" and '.tar.gz' not in ele:
            prefix = ele.rsplit('.', 1)[0]
            if prefix  not in prefix_camalari:
                prefix_camalari[prefix] = 1
                file_list.append(prefix)
        elif ele.endswith('.traineddata'):
            file_list.append(ele)
    if os.path.exists(os.path.join(model_root, model_dir, "report")):
        file_list.append("report")
    return file_list


def get_eval_status():
    dict_status = {}
    for job_id in app.eval_id2file:
        trainname, testname, config, modelname = app.eval_id2file[job_id]
        try:
            job = Job.fetch(job_id, app.redis)
            # print({'job': job, 'trainname': trainname, 'testname': testname, 'config': config, 'modelname': modelname})
            dict_status[(trainname, testname, config, modelname)] = job.get_status()
        except:
            dict_status[(trainname, testname, config, modelname)] = 'finished'
    return dict_status


def get_eval_report():
    dict_res = read_list('static/eval/eval_list')
    return dict_res


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


# Manage configure files
@app.route('/configs', methods=['GET', 'POST'], defaults={'error_message': ''})
@app.route('/configs/<error_message>', methods=['GET', 'POST'])
def manage_configs(error_message):
    print('errors:  %s' %  error_message)
    configs_list = get_configs()
    form = UploadConfigForm()
    f = form.archive.data
    errors = error_message.split('\n')
    print(errors)
    print(error_message)
    if form.validate_on_submit():
        content = f.read()
        errors = validate_string(content)
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
    return redirect(url_for('manage_data'))

@app.route('/delete_model/')
def delete_model():
    trainset = request.args.get('trainset', None)
    config = request.args.get('config', None)
    del_model_dir(trainset,  config)
    return redirect(url_for('manage_model'))

@app.route('/delete_config/<filename>')
def delete_config(filename):
    if filename in app.job_file2id:
        app.job_file2id.pop(filename, None)
    file_path = os.path.join(app.config['CONFIG_FOLDER'], filename)
    os.remove(file_path)
    return redirect(url_for('manage_configs'))


# Manage jobs
@app.route('/jobs', methods=['GET', 'POST'], defaults={'error_message': ''})
@app.route('/jobs/<error_message>', methods=['GET', 'POST'])
def manage_job(error_message):
    print('jobs')
    print(app.task_queue.job_ids)
    dict_status = get_file_status()
    dict_valid_status = get_valid_status()
    print(app.job_file2id)
    print(dict_status)
    form = SelectConfigForm()
    form.select_config.choices = get_options(get_configs())
    form.select_data.choices = get_options(get_files())
    if request.method == 'POST':
        print("form:", request.form)
        data_choices = dict(get_options(get_files()))
        config_choices = dict(get_options(get_configs()))
        print(get_configs())
        select_config = config_choices.get(form.select_config.data)
        select_data = data_choices.get(form.select_data.data)
        print('data', select_data)
        print('config:', select_config)
        if form.submit.data:
            return redirect(url_for('train_model', filename=select_data, config=select_config))
        elif form.submit_valid.data:
            return redirect(url_for('valid_model', filename=select_data, config=select_config))
    return render_template('jobs.html', form=form, dict_status=dict_status, dict_valid_status=dict_valid_status, errors = error_message)


# Manage Models
@app.route('/models/', methods=['GET', 'POST'])
def manage_model():
    error_message = ''
    model_dict = list_model_dir()
    form = UploadModelForm()
    form.select_config.choices = get_options(get_configs())
    if form.validate_on_submit() and request.method == 'POST':
        f = form.archive.data
        filename = secure_filename(f.filename)
        config_choices = dict(get_options(get_configs()))
        select_config = config_choices.get(form.select_config.data)
        trainset = 'Upload'
        model_dir = add_model(trainset, select_config)
        print('upload model:', select_config, filename, model_dir)
        if model_dir is None:
            error_message = 'Model already exists.'
            return redirect(url_for('manage_model'))
        else:
            extract_path = os.path.join(app.config['TMP_FOLDER'], filename)
            f.save(extract_path)
            print(extract_path, os.path.join(app.config['MODEL_FOLDER'], model_dir))
            extract_file(extract_path, os.path.join(app.config['MODEL_FOLDER'], model_dir))
            return redirect(url_for('manage_model'))
        # if (trainset, select_config) in model_dict:
        # return redirect(url_for('manage_data'))
    return render_template('models.html', form=form, dict_model=model_dict, error_message=error_message)


# Manage Model files
@app.route('/download_models/', methods=['GET', 'POST'])
def manage_model_list():
    trainset = request.args.get('trainset', None)
    config = request.args.get('config', None)
    model_dir = get_model_dir(trainset, config)
    file_list = get_model_list(model_dir)
    print(file_list)
    form = SelectEvalForm()
    form.select_model.choices = get_options(file_list)
    form.select_test.choices = get_options(get_files())
    if request.method == 'POST':
        print("form:", request.form)
        data_choices = dict(get_options(get_files()))
        model_choices = dict(get_options(file_list))
        print(get_configs())
        select_model = model_choices.get(form.select_model.data)

        select_test = data_choices.get(form.select_test.data)
        print('model', select_model)
        print('test:', select_test)
        return redirect(url_for('eval_model', trainname=trainset, config=config, testname=select_test,  modelname=select_model))
    return render_template('model_download.html',  form=form, trainname=trainset,  config=config, files_list=file_list)


# Manage Evals
@app.route('/evaluation', methods=['GET', 'POST'])
def manage_eval():
    dict_status = get_eval_status()
    dict_res = get_eval_report()
    dict_res = {ele:  dict_res[ele] for ele in dict_res if ele not in dict_status}
    print(app.eval_file2id)
    print(dict_status)
    return render_template('eval.html', dict_status=dict_status,  dict_res=dict_res)


# Run jobs
@app.route('/run', methods=['POST', 'GET'])
def train_model():
    print('train_model')
    filename = request.args.get('filename', None)
    config = request.args.get('config', None)
    print(filename, config)
    # form = SelectConfigForm()
    flag_new = 0
    err_msg = ''
    if (filename, config) not in app.job_file2id:
        flag_new = 1
    else:
        job_id = app.job_file2id[(filename,config)]
        job = Job.fetch(job_id, app.redis)
        status = job.get_status()
        if status != 'queued' and status != 'started':
            flag_new = 1
        else:
            err_msg = 'Job already %s.' % status
    if flag_new:
        job = app.task_queue.enqueue('engines.train.train_from_file', filename, config)
        job_id = job.get_id()
        app.job_file2id[(filename, config)] = job_id
        app.job_id2file[job_id] = (filename, config)
    print(app.job_id2file)
    # files_list = os.listdir(app.config['UPLOAD_FOLDER'])
    return redirect(url_for('manage_job', error_message=err_msg))


# Run jobs
@app.route('/eval', methods=['POST', 'GET'])
def eval_model():
    print('train_model')
    trainname = request.args.get('trainname', None)
    testname = request.args.get('testname', None)
    config = request.args.get('config', None)
    model_file = request.args.get('modelname', None)
    print(trainname, testname, config, model_file)
    flag_new = 0
    if (testname, trainname, config,  model_file) not in app.eval_file2id:
        flag_new = 1
    else:
        job_id = app.eval_file2id[(testname, trainname, config,  model_file)]
        job = Job.fetch(job_id, app.redis)
        status = job.get_status()
        if status != 'queued' and status != 'started':
            flag_new = 1
    if flag_new == 1:
        job = app.eval_queue.enqueue('engines.eval.eval_from_file', testname, trainname, config, model_file)
        job_id = job.get_id()
        app.eval_file2id[(testname, trainname, config,  model_file)] = job_id
        app.eval_id2file[job_id] = (testname, trainname, config, model_file)
    print(app.eval_id2file)
    return redirect(url_for('manage_eval'))


# # Run jobs
@app.route('/valid', methods=['POST', 'GET'])
def valid_model():
    print('valid_model')
    trainset = request.args.get('filename', None)
    config = request.args.get('config', None)
    print(trainset, config)
    if (trainset, config) not in app.job_file2id:
        return redirect(url_for('manage_job', error_message='Job is not running.'))
    else:
        job_id = app.job_file2id[(trainset, config)]
        job = Job.fetch(job_id, app.redis)
        status = job.get_status()
        print('status', status)
        if status == 'queued':  # Not start training yet
            return redirect(url_for('manage_job', error_message='Job has not started yet'))
        elif status == 'failed': # Training job failed
            return redirect(url_for('manage_job', error_message='Job Failed'))
        else:
            if (trainset, config) not in app.valid_file2id:
                job = app.valid_queue.enqueue('engines.valid.valid_from_file', trainset, config)
                job_id = job.get_id()
                app.valid_file2id[(trainset, config)] = job_id
                app.valid_id2file[job_id] = (trainset, config)
                print(app.valid_id2file)
                return redirect(url_for('manage_job'))
            else:
                job_id = app.valid_file2id[(trainset, config)]
                job = Job.fetch(job_id, app.redis)
                status = job.get_status()
                print('valid_status', status)
                if status == 'queued':
                    return redirect(url_for('manage_job', error_message='Validation job already in queue'))
                else:
                    job = app.valid_queue.enqueue('engines.valid.valid_from_file', trainset, config)
                    job_id = job.get_id()
                    app.valid_file2id[(trainset, config)] = job_id
                    app.valid_id2file[job_id] = (trainset, config)
                    print(app.valid_id2file)
                    return redirect(url_for('manage_job'))


def tardir(path, tar_name):
    with tarfile.open(tar_name, "w:gz") as tar_handle:
        for root, dirs, files in os.walk(path):
            for file in files:
                tar_handle.add(os.path.join(root, file))


@app.route('/download/', methods=['GET', 'POST'])
def download():
    trainset = request.args.get('trainname', None)
    config = request.args.get('config', None)
    model_dir = get_model_dir(trainset, config)
    file_name = request.args.get("filename", None)
    config_content = read_json(os.path.join(config_root, config))
    print(config_content["engine"])
    if config_content["engine"] == 'tesseract':
        if '.traineddata' in file_name:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
        else:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, "checkpoint", file_name)
    elif config_content["engine"] == "calamari":
        if file_name != 'report':
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name + '.tar.gz')
            if os.path.exists(out_file):
                os.remove(out_file)
            files = os.listdir(os.path.join(model_root,  model_dir))
            files = [os.path.join(model_root, model_dir, ele) for ele in files if ele.startswith(file_name)]
            compress_file(files, out_file)
            file_name += '.tar.gz'
        else:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
    else:
        out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
    return send_file(out_file, attachment_filename=file_name, as_attachment=True)

@app.route('/delete/', methods=['GET', 'POST'])
def delete():
    trainset = request.args.get('trainname', None)
    config = request.args.get('config', None)
    model_dir = get_model_dir(trainset, config)
    file_name = request.args.get("filename", None)
    config_content = read_json(os.path.join(config_root, config))
    if config_content["engine"] == 'tesseract':
        if file_name.endswith('.traineddata'):
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
        else:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, "checkpoint", file_name)
        os.remove(out_file)
    elif config_content["engine"] == 'calamari':
        files = os.listdir(os.path.join(os.getcwd(), model_root,  model_dir))
        files = [os.path.join(model_root, model_dir, ele) for ele in files if ele.startswith(file_name)]
        for out_file in files:
            os.remove(out_file)
    else:
        out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
        os.remove(out_file)
    return redirect(url_for('manage_model_list', trainset=trainset,  config=config))

@app.route('/upload/', methods=['GET', 'POST'])
def upload():
    trainset = request.args.get('trainname', None)
    config = request.args.get('config', None)
    model_dir = get_model_dir(trainset, config)
    file_name = request.args.get("filename", None)
    config_content = read_json(os.path.join(config_root, config))
    print(config_content["engine"])
    if config_content["engine"] == 'tesseract':
        if '.traineddata' in file_name:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
        else:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, "checkpoint", file_name)
    elif config_content["engine"] == "calamari":
        if file_name != 'report':
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name + '.tar.gz')
            if os.path.exists(out_file):
                os.remove(out_file)
            files = os.listdir(os.path.join(model_root,  model_dir))
            files = [os.path.join(model_root, model_dir, ele) for ele in files if ele.startswith(file_name)]
            compress_file(files, out_file)
            file_name += '.tar.gz'
        else:
            out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
    else:
        out_file = os.path.join(os.getcwd(), model_root, model_dir, file_name)
    print('uploading...')
    publish_model(
        access_token=app.token,
        model_file=out_file, # local path
        remote_file='my_image.jpg', # remote name (no path)
        ocr_engine=config_content["engine"], # OCR engine which can run the model
        license_name='WTFPL', # it seems that Zenodo recognizes acronyms, such as this one
        metadata={ # insert whatever you want in this map
            'info': 'this map can contain anything; if you do not want it, set it to none',
            'content': 'ideally it should contain all information about the training data, the parameters, the result accuracy, ...',
            'usage': 'this gets uploaded as metadata.json along with the model'
        },
        related_DOI=[('cites', '123')], # should other DOI be refered to, add them here as pairs (link, doi), otherwise set this to None
        is_draft=True # if true, then the publish request will not be sent and the upload will stay as a draft
    )
    print('uploaded!')
    return redirect(url_for('manage_model_list', trainset=trainset,  config=config))

    # return send_file(out_file, attachment_filename=file_name, as_attachment=True)

@app.route('/show_file', methods=['GET', 'POST'])
def show_content():
    file_name = request.args.get("filename", None)
    file_type = request.args.get("type", None)
    data_dir = request.args.get("file_dir", None)
    print(file_name, file_type, data_dir)
    if file_type == "config":
        text = open(os.path.join(config_root, file_name), 'r', encoding="utf-8")
        content = text.read()
        text.close()
    elif file_type == "report":
        text = open(os.path.join(model_root, data_dir, file_name), 'r', encoding="utf-8")
        content = text.read()
        text.close()
    elif file_type == 'eval':
        with open(os.path.join(eval_root, file_name), 'r', encoding="utf-8") as f_:
            content = f_.read()
    return render_template('content.html', response=content)


@app.route('/show_report', methods=['GET', 'POST'])
def show_report():
    trainset = request.args.get("filename", None)
    config = request.args.get("config", None)
    model_dir = get_model_dir(trainset, config)
    filename = 'report'
    print(trainset, config, model_dir)
    text = open(os.path.join(os.getcwd(), model_root, model_dir, filename), 'r', encoding="utf-8")
    content = text.read()
    text.close()
    return render_template('content.html', response=content)


# Manual of Using OCR Engines
@app.route('/', methods=['GET', 'POST'], defaults={'engine': 'kraken'})
@app.route('/<engine>',  methods=['GET', 'POST'])
def manual(engine):
    print(engine)
    if engine not in ['kraken', 'tesseract', 'calamari', 'ocropus']:
        help_info = ''
    else:
        help_info = read_help_information_html(engine)
    form = SelectEngineForm()
    if request.method == 'POST':
        engine_choices = dict(get_options(get_engines()))
        select_engine = engine_choices.get(form.select_engine.data)
        print('engine', select_engine)
        return redirect(url_for('manual', engine=select_engine))
    return render_template('manual.html', form=form, engine=engine, help_info=help_info)


# Model info
@app.route('/manual_model',  methods=['GET', 'POST'])
def get_model_info():
    print('train_model')
    engine = request.args.get('engine_name', None)
    print("current engine", engine)
    help_info = read_model_param(engine)
    return render_template('model.html', engine=engine, help_info=help_info)


@app.route("/results", methods=['GET'])
def get_results():
    testname = request.args.get('testname', None)
    configname = request.args.get('configname', None)
    trainname = request.args.get('trainname', None)
    modelname = request.args.get('modelname', None)
    dict_eval = read_list('static/eval/eval_list')
    key = (testname, trainname, configname, modelname)
    res_file = dict_eval[key]
    return redirect(url_for('show_content', filename=res_file, file_dir='', type='eval'))

@app.route("/download_evaluation", methods=['GET'])
def download_results():
    print('begin to download')
    testname = request.args.get('testname', None)
    configname = request.args.get('configname', None)
    trainname = request.args.get('trainname', None)
    modelname = request.args.get('modelname', None)
    dict_eval = read_list('static/eval/eval_list')
    key = (testname, trainname, configname, modelname)
    res_file = dict_eval[key]
    print('download',   res_file)
    out_file = os.path.join(os.getcwd(), eval_root,  res_file + '.tar.gz')
    return send_file(out_file, attachment_filename=res_file  +  'tar.gz', as_attachment=True)

@app.route("/delete_evaluation", methods=['GET'])
def delete_results():
    testname = request.args.get('testname', None)
    configname = request.args.get('configname', None)
    trainname = request.args.get('trainname', None)
    modelname = request.args.get('modelname', None)
    dict_eval = read_list('static/eval/eval_list')
    key = (testname, trainname, configname, modelname)
    if key in dict_eval:
        res_file = dict_eval[key]
        report_file = os.path.join(eval_root,  res_file)
        print('delete_results', report_file)
        if os.path.exists(report_file):
            os.remove(report_file)

        out_file = report_file + '.tar.gz'
        if os.path.exists(out_file):
            os.remove(out_file)
        update_list('static/eval/eval_list', res_file)
    return redirect(url_for('manage_eval'))