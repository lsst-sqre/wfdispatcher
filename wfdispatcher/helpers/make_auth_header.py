from .make_mock_user import make_mock_user
from jose import jwt


def make_auth_header():
    user = make_mock_user()
    claims = user.auth_state['claims']
    token = jwt.encode(claims, 'dummy')
    header = 'X-Portal-Authorization: bearer {}'.format(token)
    return header
