import hashlib
import fnmatch
import os.path
import re
from datetime import datetime

import eve
from eve.auth import BasicAuth
from flask import g, current_app as app

_entry_match = None
def check_access_list(email):
    """Checks the access list in the access_list.txt file for whether the
    given email address has access to the system.

    The access list should contain entries one per line. Each is an email
    address to allow, or a glob pattern to match on an email address.

    Glob special characters:
    * matches everything
    ? matches any single character
    [seq] matches any character in seq
    [!seq] matches any character not in seq

    The globs are probably only useful for matching e.g. *@ncsu.edu

    :param email: the email address to check
    :returns: True if the user has access, False if they don't.

    """
    global _entry_match
    if _entry_match is None:
        # Load in the access list. Look in the same directory as this file for
        # an access_list.txt
        entries = []
        acl = open(os.path.join(os.path.dirname(__file__), "access_list.txt"))
        with acl:
            for line in acl:
                # Strip out comments and whitespace
                line = line.split("#",1)[0].strip()
                # Ignore blank lines
                if not line:
                    continue
                # Convert from a glob pattern to a regular expression
                entries.append(fnmatch.translate(line))

        # Compile a regex object from the union of all the expressions
        _entry_match = re.compile("|".join(entries))

    return _entry_match.match(email) is not None

class SocasterAuth(BasicAuth):
    def check_auth(self, username, password, allowed_roles, resource, method):
        # use Eve's own db driver; no additional connections/resources are used
        users = app.data.driver.db['users']
        email, name = re.match("([^\|]*)\|?([^\|]*)", username).groups() #match email|name

        # Check access list
        if not check_access_list(email):
            return False

        user = users.find_one({'email': email})
        if user:
            g.user = user
            self.set_request_auth_value(email)
            return hashlib.md5(password).hexdigest() == user['auth_hash']
        else:
            auth_hash = hashlib.md5(password).hexdigest()
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
            g.user['_id'] = app.data.insert('users', g.user)
            return True
