from flask import Flask
import rq
from redis import Redis
from app.lib.job import Job

from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.redis = Redis.from_url('redis://')
app.task_queue = rq.Queue('ocr-tasks', connection=app.redis, default_timeout=43200)
app.task_queue.empty()
app.eval_queue = rq.Queue('ocr-evals', connection=app.redis, default_timeout=43200)
app.eval_queue.empty()
app.valid_queue = rq.Queue('ocr-tasks-valids', connection=app.redis, default_timeout=43200)
app.valid_queue.empty()

app.job_id2file = {}
app.job_file2id = {}
app.job_id2err = {}

app.eval_id2file = {}
app.eval_file2id = {}
app.eval_id2err = {}

app.valid_id2file = {}
app.valid_file2id = {}
app.valid_id2err = {}

model_root = 'static/model'
data_root = 'static/data'
config_root = 'static/configs'
eval_root = 'static/eval'

from app import routes
from app.api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')