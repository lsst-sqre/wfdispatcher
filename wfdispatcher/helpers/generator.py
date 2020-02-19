from .make_auth_header import make_auth_header
from .make_post_body import make_post_body


class Generator(object):
    bodyfile = "postbody.json"
    headerfile = "authheader.txt"
    _mock = False

    def __init__(self, *args, **kwargs):
        _mock = kwargs.pop('_mock', self._mock)
        self._mock = _mock
        bodyfile = kwargs.pop('body', self.bodyfile)
        self.bodyfile = bodyfile
        headerfile = kwargs.pop('header', self.headerfile)
        self.headerfile = headerfile

    def go(self):
        print(make_auth_header(_mock=self._mock),
              file=open(self.headerfile, 'w'))
        print(make_post_body(), file=open(self.bodyfile, 'w'))
