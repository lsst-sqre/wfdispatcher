import json
from urllib.parse import quote


class User(object):
    '''This looks a little like the JupyterHub User object, but is not one.

    It has the following attributes:
      name (str)
      escaped_name (str)
      namespace (str)
      uid (int)
      access_token (str)
      claims (dict)

    However, unlike the JupyterHub User, there's no backing ORM.

    The only place we substitute one of these for a JupyterHub User is in
    create_workflow, and we only use the escaped_name field for it.
    '''

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop('name', None)
        if self.name:
            self.escaped_name = quote(self.name)
        self.namespace = kwargs.pop('namespace', None)
        self.uid = kwargs.pop('uid', None)
        self.access_token = kwargs.pop('access_token', None)
        self.claims = kwargs.pop('claims', None)

    def dump(self):
        rv = {
            "name": self.name,
            "escaped_name": self.escaped_name,
            "namespace": self.namespace,
            "uid": self.uid,
            "access_token": "<REDACTED>"
        }
        cc = {}.update(self.claims)
        tok = cc.get('access_token', None)
        if tok:
            cc['access_token'] = "<REDACTED>"
        rv["claims"] = cc
        return rv

    def toJSON(self):
        return json.dumps(self.dump())
