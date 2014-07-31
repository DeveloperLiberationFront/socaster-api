import bcrypt, re, eve, flask
from eve.auth import BasicAuth
from flask import g
from datetime import datetime

class SocasterAuth(BasicAuth):
    def check_auth(self, username, password, allowed_roles, resource, method):
        # use Eve's own db driver; no additional connections/resources are used
        app = flask.current_app
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
                'roles': ['user'],
                eve.DATE_CREATED: dt,
                eve.LAST_UPDATED: dt
            }
            app.data.insert('users', g.user)
            return True
