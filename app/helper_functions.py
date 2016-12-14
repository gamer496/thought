import config
import os
from flask import render_template

def comp(data):
    if not data.has_key("from"):
        data["from"] = 1
    else:
        data["from"] = int(data["from"])
    if not data.has_key("posts_per_page"):
        data["posts_per_page"] = config.POSTS_PER_PAGE
    else:
        data["posts_per_page"] = int(data["posts_per_page"])
    return data

def manual_paginate_count(obj, start, posts_per_page, flag = False):
    if flag:
        length = len(obj)
    else:
        length = obj.count()
    start -= 1
    if start >= length:
        return [[],0]
    ans = []
    for i in range(start, start + posts_per_page):
        if i >= length:
            break
        ans.append(obj[i].half_serialize())
    return [ans, length]
