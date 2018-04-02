#!/usr/bin/python
################################################################################
# VIEW
#
# Justin Dierking
# justin.l.dierking.civ@mail.mil
# (614) 692 2050
#
# 10/25/2016 Original construction
################################################################################

import jinja2
    
def index_view():
    templateLoader = jinja2.FileSystemLoader( searchpath="./dev5/view/templates")
    templateEnv = jinja2.Environment( loader=templateLoader )
    template = templateEnv.get_template('index2.html')
    return template.render()
    