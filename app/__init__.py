from flask import Flask
import rq
from redis import Redis

from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.redis = Redis.from_url('redis://')
app.task_queue = rq.Queue('ocr-tasks', connection=app.redis,default_timeout=43200)

from app import routes