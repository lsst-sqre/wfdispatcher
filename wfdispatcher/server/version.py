import falcon
from eliot import log_call
from .._version import __version__
from rubin_jupyter_utils.hub import Loggable


class Version(Loggable):
    @log_call
    def on_get(self, req, resp):
        self.log.debug("Returning version.")
        resp.media = {"version": __version__}
        resp.status = falcon.HTTP_200
