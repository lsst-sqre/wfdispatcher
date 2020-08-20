from .make_auth_header import make_auth_header
from .make_post_body import make_post_body


class Generator(object):
    def __init__(self, *args, **kwargs):
        self._mock = kwargs.pop("_mock", False)
        self.bodyfile = kwargs.pop("body", "postbody.json")
        self.headerfile = kwargs.pop("header", "authheader.txt")

    def go(self):
        print(
            make_auth_header(_mock=self._mock), file=open(self.headerfile, "w")
        )
        print(make_post_body(), file=open(self.bodyfile, "w"))
