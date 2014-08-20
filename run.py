#!/usr/local/bin/python2.7

import os
from setproctitle import setproctitle
setproctitle('socaster-api')

if os.geteuid() == 0:
    #write pidfile for use as daemon
    pidfile = open("/var/run/socaster-api.pid", "w")
    pidfile.write(str(os.getpid()))
    pidfile.close()

import eve, simplejson as json
from eve import Eve
from flask import g, abort, request, make_response, redirect
from datetime import datetime

from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import options

import yampy
from bson.objectid import ObjectId

from validator import Validator
from auth import SocasterAuth

#set up logging for tornado + copy logs to mongo
import logging
options.logging = 'debug'
options.log_to_stderr = True
options.parse_command_line()
logger = logging.getLogger('tornado.access')

# Mongo logging
# import logging
# from mongolog.handlers import MongoHandler
# handler = MongoHandler.to(db='socaster', collection='log',
#                           username='eve', password='api service access')
# for name in ['tornado.access', 'tornado.application', 'tornado.general']:
#     logging.getLogger(name).addHandler(handler)

app = Eve(auth=SocasterAuth, validator=Validator)

def get_list_field(resource, name):
    fields = app.config['DOMAIN'][resource].get(name, None)
    if not fields: return []
    if not isinstance(fields, list): fields = [fields]
    return fields

def restrict_access(resource, request, lookup):
    fields = get_list_field(resource, 'restrict_access')
    if not fields or 'admin' in g.user['roles']: return #admins can read anything

    #restrict results to only those the user is allowed to read
    lookup['$or'] = []
    for field in fields:
        lookup['$or'].extend([
            {field: {"$elemMatch": {"$in": [g.user['email'], g.user['_id'], 'public']}}},
            {field: {"$in": [g.user['email'], g.user['_id'], 'public']}}
        ])

def restrict_update(resource, item, original=None):
    fields = get_list_field(resource, 'restrict_update')
    if not fields or 'admin' in g.user['roles']: return #admins can update anything

    found = False
    for field in fields:
        logger.debug(field)
        value = original[field] if original else item[field]
        if (isinstance(value, list) and (g.user['email'] in value or g.user['_id'] in value)) \
           or g.user['email'] == value or g.user["_id"] == value:
            found = True

    if not found: abort(403)

def set_creator(resource, items):
    fields = get_list_field(resource, 'creator')
    if not fields: return
    for field in fields:
        field_type = app.config['DOMAIN'][resource]['schema'][field]['type']
        for item in items:
            if field_type is 'objectid':
                item[field] = g.user['_id']
            else:
                item[field] = g.user['email']

def prevent_escalation(item, original=None):
    if 'roles' in item and 'admin' not in g.user.get('roles', []):
        abort(403, 'You do not have permission to set roles')

def require_admin(*args):
    if 'admin' not in g.user['roles']:
        abort(403, 'This action requires admin privileges')

def multi_unique(resource, items, original=None):
    fields = get_list_field(resource, 'unique')
    if not isinstance(items, list): items = [items]
    if not fields: return
    for item in items:
        query = {'_id': {'$ne': item['_id']}} if item.has_key('_id') else {}
        for field in fields:
            query[field] = item[field]
        if app.data.find_one(resource, None, **query):
            abort(400, 'These fields must be unique: %s' % fields)

def restrict_image_access(request, lookup):
    clip = app.data.find_one_raw('clips', request.view_args['clip'])
    if clip and g.user['email'] not in clip['share'].append(clip['user']) and 'public' not in clip['share']:
        abort(403, "You do not have access to the frames for this clip")

def insert_events(items):
    db = app.data.driver.db
    for item in items:
        tool = db.tools.find_one({'name': item['tool'], 'application': item['application']})
        if not tool: abort(400, 'Tool does not exist')

        item['description'] = tool['_id']
        item['user_id'] = g.user['email']

    user = db.users.find_one({'_id': g.user['_id']})
    if not user: abort(400, 'User does not exist?')

    now = datetime.now()
    user.update({
        'user_id': user['email'],
        'last_upload_date': now,
        eve.LAST_UPDATED: now
    })
    db.users.update({'_id': user['_id']}, user)

@app.route('/report-usage', methods=['POST', 'PUT'])
def record_bulk_usage():
    if not app.auth.authorized([], '', request.method):
        return app.auth.authenticate()

    db = app.data.driver.db
    #usages: [{app_name: str, tool_name: str, keyboard: int, mouse: int}]
    usages = request.get_json()
    v = Validator({
        'app_name': {'type': 'string', 'required': True},
        'tool_name': {'type': 'string', 'required': True},
        'keyboard': {'type': 'integer'},
        'mouse': {'type': 'integer'}
    })
    if not usages or not isinstance(usages, list):
        abort(400, "Please supply a list of usages")

    if not all(map(v.validate, usages)):
        abort(400, 'You must supply usage data in the form [{app_name: str, tool_name: str, keyboard: int, mouse: int}, ...]')

    apps = set()
    for usage in usages:
        apps.add(usage['app_name']) #collect set of applications for adding later
        tool_desc =  {
            'application': usage['app_name'],
            'name': usage['tool_name'],
        }
        tool = db.tools.find_one(tool_desc)
        if not tool:
            tool = db.tools.update(tool_desc, tool_desc, upsert=True)
        tool_id = tool.get('_id', tool.get('upserted'))

        #add user to tool user set
        db.tools.update({'_id': tool_id},
                        {'$addToSet': {'users': g.user['email']}})

        db.usages.update({'tool': tool_id, 'user': g.user['email']}, {
            'tool': tool_id,
            'user': g.user['email'],
            'keyboard': usage.get('keyboard', 0),
            'mouse': usage.get('mouse', 0),
            eve.LAST_UPDATED: datetime.now()
        }, upsert=True)
        
    for name in apps:
        db.applications.update({'name': name}, {'$set': {'name': name}}, upsert=True)

    return make_response(json.dumps({
        'message': 'Usages were uploaded successfully',
        '_status': 'OK',
        '_code': '201'
    }), 201)


@app.route('/yammer-login', methods=["OPTIONS"])
def options():
    return make_response("", 200, {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type"})

@app.route('/yammer-login', methods=["GET"])
def yammer_login():
    if not app.auth.authorized([], '', request.method):
        return app.auth.authenticate()

    authenticator = yampy.Authenticator(client_id="h3V8HGfIF8Cue8QHnJRDJQ", client_secret="NihCDhkZU0fszQ0H7ZHG5Gsr7qQGuLhQBrgaBmskl4")
    auth_url = authenticator.authorization_url(redirect_uri="http://recommender.oscar.ncsu.edu/api/v2/yammer-login/" + str(g.user["_id"]))
    
    return make_response(json.dumps({
        'url': auth_url,
    }), 200, {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "Authorization, Content-Type"})

@app.route("/yammer-login/<id>")
def yammer_login_id(id):
    if "code" in request.args:
        authenticator = yampy.Authenticator(client_id="h3V8HGfIF8Cue8QHnJRDJQ", client_secret="NihCDhkZU0fszQ0H7ZHG5Gsr7qQGuLhQBrgaBmskl4")
        code = request.args["code"];
        db = app.data.driver.db

        try:
            user = db.users.find_one({"_id": ObjectId(id)})
            if user:
                yammer_access_token = authenticator.fetch_access_token(code)
                db.yammer_tokens.update({"user": user["email"]}, {"user": user["email"], "token": yammer_access_token}, upsert=True)

                return redirect("http://localhost:4443/#/status", 201)
            else:
                return redirect("http://localhost:4443/#/status", 401)
        except:
            return redirect("http://localhost:4443/#/status", 401)
                
if __name__ == '__main__':
    
    app.debug = True

    app.on_delete_resource += require_admin

    app.on_pre_GET += restrict_access

    app.on_replace += restrict_update
    app.on_update += restrict_update
    app.on_delete_item += restrict_update

    app.on_insert += set_creator

    app.on_update += multi_unique
    app.on_insert += multi_unique

    app.on_update_users += prevent_escalation
    app.on_replace_users += prevent_escalation

    app.on_pre_GET_images += restrict_image_access

    app.on_insert_events += insert_events

    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()
    # app.run()
