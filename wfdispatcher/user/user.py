import json
from urllib.parse import quote


class User(object):
    """This looks a little like the JupyterHub User object, but is not one.

    It has the following attributes:
      name (str)
      escaped_name (str)
      namespace (str)
      uid (int)
      access_token (str)
      groups (list of str)
      claims (dict)

    However, unlike the JupyterHub User, there's no backing ORM.

    The only place we substitute one of these for a JupyterHub User is in
    create_workflow.  We use the escaped_name and groups fields for that.
    (Groups is indirect via the quota manager.)
    """

    def __init__(self, *args, **kwargs):
        self.name = kwargs.pop("name", None)
        if self.name:
            self.escaped_name = quote(self.name)
        self.namespace = kwargs.pop("namespace", None)
        self.uid = kwargs.pop("uid", None)
        self.access_token = kwargs.pop("access_token", None)
        self.claims = kwargs.pop("claims", None)
        self.groups = self._groups_from_claims()

    def _groups_from_claims(self):
        # Only return groups with matching gids
        if not self.claims:
            return None
        # We assume a CILogon-style "isMemberOf"
        imo = self.claims.get("isMemberOf")
        if not imo:
            return None
        gnames = [x["name"] for x in imo if "id" in x]
        return gnames

    def dump(self):
        rv = {
            "name": self.name,
            "escaped_name": self.escaped_name,
            "namespace": self.namespace,
            "uid": self.uid,
            "groups": self.groups,
            "access_token": "<REDACTED>",
        }
        cc = {}
        if self.claims:
            cc.update(self.claims)
        tok = cc.get("access_token", None)
        if tok:
            cc["access_token"] = "<REDACTED>"
        rv["claims"] = cc
        return rv

    def toJSON(self):
        return json.dumps(self.dump())
