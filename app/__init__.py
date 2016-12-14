from flask import Flask, Blueprint
from flask_script import Manager
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth

blog  = Flask(__name__)
db = SQLAlchemy(blog)
manager = Manager(blog)
blog.config.from_object('config')
migrate = Migrate(blog, db)
CORS(blog)
auth = HTTPBasicAuth()

from app import models, views