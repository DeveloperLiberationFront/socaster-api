import bcrypt
import re
import eve
from eve import Eve
from eve.auth import BasicAuth
from flask import g, abort
from datetime import datetime

class BCryptAuth(BasicAuth):
    def check_auth(self, username, password, allowed_roles, resource, method):
        # use Eve's own db driver; no additional connections/resources are used
        users = app.data.driver.db['users']
        email, name = re.match("([^\|]*)\|?([^\|]*)", username).groups() #match email|name
        user = users.find_one({'email': email})
        if user:
            g.user = user
            self.set_request_auth_value(email)
            return bcrypt.hashpw(password, user['auth_hash']) == user['auth_hash']
        else:
            auth_hash = bcrypt.hashpw(password, bcrypt.gensalt())
            self.set_request_auth_value(email)
            dt = datetime.now()
            g.user = {
                'name': name,
                'email': email,
                'auth_hash': auth_hash,
                eve.DATE_CREATED: dt,
                eve.LAST_UPDATED: dt
            }
            app.data.insert('users', g.user)
            return True

def get_list_field(resource, name):
    fields = app.config['DOMAIN'][resource].get(name, None)
    if not fields: return []
    if not isinstance(fields, list): fields = [fields]
    return fields

def restrict_access(resource, request, lookup):
    fields = get_list_field(resource, 'restrict_read')
    if not fields or 'admin' in g.user['roles']: return #admins can read anything
    #restrict results to only those the user is allowed to read
    lookup['$or'] = []
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
        value = original and original[field] or item[field]
        if (isinstance(value, list) and g.user['email'] in value) or g.user['email'] == value:
            found = True

    if not found: abort(403)

def set_creator(resource, items):
    fields = get_list_field(resource, 'creator')
    if not fields: return
    for field in fields:
        for item in items:
            item[field] = g.user['email']

    print items

def prevent_escalation(item, original=None):
    if 'admin' not in g.user.get('roles', []):
        abort(403, 'You do not have permission to set roles')
        #item.pop('roles', None) #don't let non-admins set roles via api

if __name__ == '__main__':
    app = Eve(auth=BCryptAuth)
    app.debug = True

    app.on_pre_GET += restrict_access
    app.on_replace += restrict_update
    app.on_update += restrict_update
    app.on_delete_item += restrict_update
    app.on_insert += set_creator

    app.on_update_users += prevent_escalation
    app.on_replace_users += prevent_escalation

    app.run()
