from app import blog, db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_utils import ScalarListType, force_auto_coercion
from datetime import datetime
import json
import uuid
import ipdb


force_auto_coercion()


class Blog(db.Model):
	__tablename__ = "blog"
	id					=db.Column			(db.Integer, primary_key = True)
	title					=db.Column			(db.String(250), unique = True, index = True)
	content					=db.Column			(db.Text)
	created_on				=db.Column			(db.DateTime)
	updated_on				=db.Column			(db.DateTime)
	publish					=db.Column			(db.Boolean)
	comments				=db.relationship	('Comment', backref = "blog", lazy = "dynamic")

	def __init__(self, title):
		self.title = title
		self.publish = False

	def __repr__(self):
		return "Blog: " + str(self.title)


class Admin(db.Model):
	__tablename__ = "admin"
	id					=db.Column			(db.Integer, primary_key = True)
	username 				=db.Column			(db.String(200), unique = True, index = True)
	password  				=db.Column			(db.String(200))
	created_on				=db.Column			(db.DateTime)
	updated_on				=db.Column			(db.DateTime)
	active					=db.Column			(db.Boolean)

	def __init__(self, username, password):
		self.username = username
		self.created_on = datetime.utcnow()
		self.set_password(password)
		self.active = True

	def set_password(self, password):
		self.password = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password, password)

	def generate_auth_token(self):
		s = Serializer(blog.config['SECRET_KEY'], expires_in = 5184000)
		return s.dumps({"id": self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(blog.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except BadSignature:
			return None
		user = Admin.query.get(data["id"])
		return user

	def half_serialize(self):
		d = {}
		d["id"] = self.id
		d["username"] = self.username
		return d

	def full_serialize(self):
		d = self.half_serialize()
		d["created_on"] = self.created_on
		return d

	def __repr__(self):
		return "Admin: " + str(self.username)

class Log(db.Model):
	__tablename__ = "log"
	id						=db.Column		(db.Integer, primary_key = True)
	ip_addr						=db.Column		(db.String(200))
	visited_on					=db.Column		(db.DateTime)
	route						=db.Column		(db.String(200))

	def __init__(self, addr):
		self.ip_addr = addr
		self.visited_on = datetime.utcnow()

	def __repr__(self):
		return "Log: " + str(ip_addr) + "on" + str(visted_on)

class Comment(db.Model):
	__tablename__ = "comment"
	id						=db.Column		(db.Integer, primary_key = True)
	blog_id						=db.Column		(db.Integer, db.ForeignKey('blog.id'))
	content						=db.Column		(db.Text)
	ip_addr						=db.Column		(db.String(200))

	def __init__(self, content):
		self.content = content

	def half_serialize(self):
		d = {}
		d["id"] = self.id
		d["content"] = self.content
		d["ip_addr"] = self.ip_addr
		return d

	def full_serialize(self):
		d = self.half_serialize()
		return d

	def __repr__(self):
		return "Comment: " + str(self.id)
