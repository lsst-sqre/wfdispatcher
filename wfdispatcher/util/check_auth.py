'''Check the authentication header and either return an appropriate user
or raise an error.
'''

import falcon
from ..user.user import User

HEADER_NAME = "X-Portal-Authorization"


def check_auth(req):
    '''Read the request headers and either construct a user from them,
    or raise an error.

    'req' is a Falcon request.
    '''
