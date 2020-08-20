import datetime
import grp
import os
import pwd
from ..user.user import User


def make_user_from_env():
    exp = datetime.datetime(2050, 1, 1, tzinfo=datetime.timezone.utc)
    user = User()
    user.name = os.getenv("USER")
    user.escaped_name = user.name
    pwn = pwd.getpwnam(user.name)
    groupmap = {}
    for g in grp.getgrall():
        if user.name in g.gr_mem:
            groupmap[g.gr_name] = g.gr_gid
    claims = {
        "uid": user.name,
        "uidNumber": pwn.pw_uid,
        "exp": int(exp.timestamp()),
    }
    imo = []
    for gname in groupmap:
        imo.append({"name": gname, "id": groupmap[gname]})
    claims["isMemberOf"] = imo
    user.auth_state = {
        "groupmap": groupmap,
        "uid": user.name,
        "claims": claims,
    }
    user.groups: list(claims["groupmap"].keys())
    return user
