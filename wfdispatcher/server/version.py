import falcon
from .._version import __version__
from jupyterhubutils import Loggable


class Version(Loggable):

    def on_get(self, req, resp):
        self.log.debug("Returning version.")
        resp.media = {'version': __version__}
        resp.status = falcon.HTTP_200
