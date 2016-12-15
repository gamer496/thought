from app import blog, db, auth
from models import *
from flask import jsonify, request, url_for, g
from flask_weasyprint import HTML, render_pdf
import os
from datetime import datetime
import helper_functions
import json
import random
import ipdb
import config

@blog.errorhandler(404)
def page_not_found(e = ""):
    return jsonify({"err": "404 error page not found"}),404

@blog.errorhandler(403)
def not_authorized(e = ""):
    return jsonify({"err": "You are not authorized to view this page"}),403

@blog.errorhandler(400)
def something_missing(e = ""):
    return jsonify({"err": "Arguments provided were not enough to carry out this request"}),400


def internal_error(s = ""):
    return jsonify({"err": "internal server error.","description": s}),500

def as_msg(s, errors = []):
    return jsonify({"err": "There seems to be some error","description": s,"errors": errors})

def as_success(s, warnings = [], errors = [], di = {}):
    d = di
    if not len(errors)==0:
        d["errors"]=errors
        d["partial_success"]=s
    if not len(warnings)==0:
        d["warnings"]=warnings
    if not d.has_key("partial_success"):
        d["success"]=s
    return jsonify(d)

@blog.after_request
def after_request(response):
    try:
        try:
            send_data = json.loads(response.get_data())
        except:
            send_data = {}
        try:
            data = request.json
        except:
            data = {}
        if not data:
            data = {}
        try:
            log = Log(request.remote_addr)
            log.visited_on = datetime.utcnow()
            db.session.add(log)
            db.session.commit()
        except:
            print "log information failed"
        if data.has_key("user_token"):
            send_data["user_token"] = data["user_token"]
        response.set_data(json.dumps(send_data))
        return response
    except:
        return jsonify({"msg": "internal error occurred."})


@auth.verify_password
def verify_password(token, password = None):
    user = None
    if request.json.has_key("user_token"):
        user = Admin.verify_auth_token(request.json["user_token"])
    if not user:
        return False
    else:
        if not user.active:
            return False
        g.user = user
        return True

@blog.route("/index",methods = ["GET","POST"])
@blog.route("/",methods = ["GET","POST"])
def index():
    return jsonify({"msg": "kamehameha"})

@blog.route("/show_blogs", methods = ["GET", "POST"])
def show_blogs():
    try:
        data = request.json
    except:
        data = {}
    data = helper_functions.comp(data)
    l = helper_functions.manual_paginate_count(Blog.query.filter(Blog.publish == True), data["from"], data["posts_per_page"])
    return jsonify({"blogs": l[0], "count": l[1]})

@blog.route("/show_blog", methods = ["GET","POST"])
def show_blog():
    try:
        blog_id = int(data["blog_id"])
    except:
        return page_not_found()
    blog = Blog.query.get(blog_id)
    if not blog:
        return as_msg("no such blog found")
    return jsonify({"blog": blog.full_serialize()})

@blog.route("/login", methods = ["GET", "POST"])
def login():
    try:
        data = request.json
    except:
        return page_not_found()
    if not data.has_key("username"):
        return page_not_found()
    if not data.has_key("password"):
        return page_not_found()
    user = Admin.query.filter(Admin.username == data["username"].strip())
    if not user:
        return page_not_found()
    if not user.check_password(data["password"].strip()):
        return page_not_found()
    user_token = user.generate_auth_token()
    return jsonify({"user_token": user_token})

@blog.route("/register_new_user", methods = ["GET", "POST"])
@auth.login_required
def register_new_user():
    try:
        data = request.json
    except:
        return page_not_found()
    try:
        username = data["username"].strip()
        users = Admin.query.filter(Admin.username == username)
        if not users.count() == 0:
            return as_msg("user with this name already exists")
        password = data["password"].strip()
        user = Admin(username = username, password = password)
        try:
            db.session.add(user)
            db.session.commit()
        except:
            return as_msg("db transaction failed.")
    except:
        return internal_error()
    return as_success("new admin successfully created")

@blog.route("/deactivate_admin", methods = ["GET", "POST"])
@auth.login_required
def deactivate_admin():
    try:
        data = request.json
    except:
        return page_not_found()
    try:
        username = data["username"].strip()
        if username == config.USERNAME:
            return as_msg("cannot deactivate super admin.")
        user = g.user
        if not user.username == username:
            return as_msg("only super admin can deactivate other users")
        to_user = Admin.query.get(Admin.username == username)
        if not to_user:
            return as_msg("no such admin present")
        to_user.active = False
        try:
            db.session.add(to_user)
            db.session.commit()
        except:
            return as_msg("db transaction failed")
    except:
        return internal_error()
    return as_success("successfully deactivated user.")

@blog.route("/add_comment", methods = ["GET", "POST"])
def add_comment():
    try:
        data = request.json
    except:
        return page_not_found()
    try:
        comment = Comment(data["content"].strip())
        comment.ip_addr = request.remote_addr
        comment.blog_id = int(data["blog_id"])
        try:
            db.session.add(comment)
            db.session.commit()
        except:
            return as_msg("db transaction failed")
    except:
        return internal_error()
    return as_success("successfully added comment")

@blog.route("/show_comments", methods = ["GET", "POST"])
def show_comments():
    try:
        data = request.json
    except:
        return page_not_found()
    try:
        blog = Blog.query.get(int(data["blog_id"]))
        l = helper_functions.manual_paginate_count(blog.comments, data["start"], data["posts_per_page"])
        return jsonify({"comments": l[0], "count": l[1]})
    except:
        return internal_error()

@blog.route("/create_blog", methods = ["GET", "POST"])
@auth.login_required
def create_blog():
    try:
        data = request.json
    except:
        return page_not_found()
    content = data["content"].strip()
    title = data["title"].strip()
    blogs = Blog.query.filter(Blog.title == title)
    if not blogs.count() == 0:
        return as_msg("blog of this name already exists")
    blog = Blog(title = title)
    blog.content = content
    try:
        db.session.add(blog)
        db.session.commit()
    except:
        return as_msg("db transaction failed")
    return as_success("blog successfully created.", {di = blog})

@blog.route("/publish_blog", methods = ["GET", "POST"])
@auth.login_required
def publish_blog():
    try:
        blog_id = int(data["blog_id"])
    except:
        return page_not_found()
    blog = Blog.query.get(blog_id)
    if not blog:
        return as_msg("no such blog found")
    blog.publish = True
    try:
        db.session.add(blog)
        db.session.commit()
    except:
        return as_msg("db transaction failed")
    return as_success("blog successfully published")

@blog.route("/unpublish_blog", methods = ["GET", "POST"])
@auth.login_required
def unpublish_blog():
    try:
        data = request.json
    except:
        return page_not_found()
    try:
        blog = Blog.query.get(int(data["blog_id"].strip()))
        if not blog:
            return as_msg("no such blog exists")
        blog.publish = False
        try:
            db.session.add(blog)
            db.session.commit()
        except:
            return as_msg("db transaction failed")
        return as_success("blog successfully unpublished")
    except:
        return internal_error()

@blog.route("/edit_blog", methods = ["GET","POST"])
@auth.login_required
def edit_blog():
    try:
        data = int(data["blog_id"])
    except:
        return page_not_found()
    try:
        blog = Blog.query.get(int(data["blog_id"]))
        blogs = Blog.query.get(data["title"].strip())
        if not (blog.title == data["title"].strip() and blogs.count() == 0 ):
            return as_msg("blog with this title already present")
        blog.title = data["title"].strip()
        blog.content = data["content"].strip()
        blog.updated_on = datetime.utcnow()
        try:
            db.session.add(blog)
            db.session.commit()
        except:
            return as_msg("db transaction failed")
    except:
        return as_success("blog successfully updated")

@blog.route("/check_title", methods = ["GET", "POST"])
@auth.login_required
def check_title():
    try:
        data = request.json
    except:
        return page_not_found()
    blogs = Blog.query.filter(Blog.title == data["title"].strip())
    title = config.TITLE
    if data.has_key("blog_id"):
        try:
            title = Blog.query.get(data["blog_id"].strip()).title
        except:
            title = config.TITLE
    else:
        if not (title == data["title"].strip() and blogs.count() == -1 ):
            flag = False
        else:
            flag = True
    return jsonify({"result": flag})
