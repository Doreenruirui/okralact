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
app.job_id2file = {}
app.job_file2id = {}
app.job_id2err = {}

from app import routes
from app.api import bp as api_bp
app.register_blueprint(api_bp, url_prefix='/api')