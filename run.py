import eve, simplejson as json
from eve import Eve
from flask import g, abort, request, response
from datetime import datetime
from eve.auth import requires_auth

from tornado.wsgi import WSGIContainer
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer

from validator import Validator
from auth import SocasterAuth

app = Eve(auth=SocasterAuth, validator=Validator)

def get_list_field(resource, name):
    fields = app.config['DOMAIN'][resource].get(name, None)
    if not fields: return []
    if not isinstance(fields, list): fields = [fields]
    return fields

def restrict_access(resource, request, lookup):
    fields = get_list_field(resource, 'restrict_read')
    if not fields or 'admin' in g.user['roles']: return #admins can read anything
    public = app.config['DOMAIN'][resource].get('public', None)

    #restrict results to only those the user is allowed to read
    lookup['$or'] = [{public: 'public'}] if public else []
    for field in fields:
        lookup['$or'].extend([
            {field: {"$elemMatch": {"$in": [g.user['email'], 'public']}}},
            {field: {"$in": [g.user['email'], 'public']}}
        ])

def restrict_update(resource, item, original=None):
    fields = get_list_field(resource, 'restrict_update')
    if not fields or 'admin' in g.user['roles']: return #admins can update anything

    found = False
    for field in fields:
        value = original[field] if original else item[field]
        if (isinstance(value, list) and g.user['email'] in value) or g.user['email'] == value:
            found = True

    if not found: abort(403)

def set_creator(resource, items):
    fields = get_list_field(resource, 'creator')
    if not fields: return
    for field in fields:
        for item in items:
            item[field] = g.user['email']

def prevent_escalation(item, original=None):
    if 'roles' in item and 'admin' not in g.user.get('roles', []):
        abort(403, 'You do not have permission to set roles')

def require_admin(*args):
    print args
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
    print request.args
    clip = app.data.find_one_raw('clips', lookup['clip'])
    if clip and g.user['email'] not in clip['share'].append(clip['user']) and 'public' not in clip['share']:
        abort(403, "You do not have access to the frames for this clip")

@app.route('/report-usage', methods=['POST'])
def record_bulk_usage():
    if not app.auth.authorized([], '', request.method):
        return app.authenticate()

    db = app.data.driver.db
    #usages: [{app_name: str, tool_name: str, keyboard: int, mouse: int}]
    usages = request.get_json()
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
        
        db.usages.update({'tool': tool_id, 'user': g.user['email']}, {
            'tool': tool_id,
            'user': g.user['email'],
            'keyboard': usage.get('keyboard', 0),
            'mouse': usage.get('mouse', 0),
            eve.LAST_UPDATED: datetime.now()
        }, upsert=True)
        
    for name in apps:
        db.applications.update({'name': name}, {'name': name}, upsert=True)

    response.status_code = 201
    return json.dumps({
        'message': 'Usages were uploaded successfully',
        '_status': 'OK',
        '_code': '201'
    })
                
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

    # http_server = HTTPServer(WSGIContainer(app))
    # http_server.bind(5000)
    # http_server.start(0)
    # IOLoop.instance().start()
    app.run()
