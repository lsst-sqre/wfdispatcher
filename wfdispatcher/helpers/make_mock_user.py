import datetime
from ..user.user import User


def make_mock_user():
    exp = datetime.datetime(2050, 1, 1, tzinfo=datetime.timezone.utc)
    user = User()
    user.name = "kkinnison"
    user.escaped_name = user.name
    groupmap = {"lens": 10, "public": 1000}

    claims = {"uid": user.name, "uidNumber": 1934, "exp": int(exp.timestamp())}

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
