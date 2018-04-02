#!/usr/bin/python
################################################################################
# AUTH
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 01/03/2017 Original construction
################################################################################

import jinja2

def admin_view():
    templateLoader = jinja2.FileSystemLoader(searchpath = "./dev5/view/templates")
    templateEnv = jinja2.Environment(loader = templateLoader )
    template = templateEnv.get_template('auth.html')
    return template.render()

def user_attr_view():
    templateLoader = jinja2.FileSystemLoader(searchpath = "./dev5/view/templates")
    templateEnv = jinja2.Environment(loader = templateLoader )
    template = templateEnv.get_template('userattr.html')
    return template.render()
    
def login_view(username, msg="Enter login information", from_page="/"):
    templateLoader = jinja2.FileSystemLoader(searchpath = "./dev5/view/templates")
    templateEnv = jinja2.Environment(loader = templateLoader)
    template = templateEnv.get_template('login.html')
    return template.render(username = username, msg = msg, from_page = from_page)