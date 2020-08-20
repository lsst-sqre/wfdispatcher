from .make_mock_user import make_mock_user
from .make_user_from_env import make_user_from_env
from jose import jwt


def make_auth_header(_mock=False):
    if _mock:
        user = make_mock_user()
    else:
        user = make_user_from_env()
    claims = user.auth_state["claims"]
    token = jwt.encode(claims, "dummy")
    header = "X-Portal-Authorization: bearer {}".format(token)
    return header
