import bcrypt
import re
from eve import Eve
from eve.auth import BasicAuth
from flask import g, abort

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
            g.user = {
                'name': name,
                'email': email,
                'auth_hash': auth_hash
            }
            app.data.insert('users', g.user)
            return True

def restrict_access(resource, request, lookup):
    field = app.config['DOMAIN'][resource].get('restrict_access', None)
    if field:
        #restrict results to only those the user is allowed to read
        lookup['$or'] = [
            {field: {"$elemMatch": {"$in": [g.user['email'], 'public']}}},
            {field: {"$in": [g.user['email'], 'public']}}
        ]

def restrict_update(resource, item, original):
    field = app.config['DOMAIN'][resource].get('restrict_update', None)
    print field
    if field:
        value = original[field]
        if isinstance(value, list):
            if g.user['email'] not in value:
                abort(403)
        else:
            if g.user['email'] != value:
                abort(403)

if __name__ == '__main__':
    app = Eve(auth=BCryptAuth)
    app.debug = True

    app.on_pre_GET += restrict_access
    app.on_replace += restrict_update
    app.on_update += restrict_update
    app.run()
