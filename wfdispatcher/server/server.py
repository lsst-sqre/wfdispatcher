"""Simple RESTful API server for dispatching Argo Workflows.
"""

import falcon
from ..auth.auth import AuthenticatorMiddleware as AM
from ..helpers.mockspawner import MockSpawner
from .requirejson import RequireJSONMiddleware
from .new import New
from .details import Details
from .list import List
from .logs import Logs
from .pods import Pods
from .singleworkflow import SingleWorkflow
from .version import Version
from rubin_jupyter_utils.hub import Loggable


class Server(Loggable):
    def __init__(self, *args, **kwargs):
        self.app = None
        super().__init__(*args, **kwargs)
        _mock = kwargs.pop("_mock", False)
        self._mock = _mock
        if _mock:
            self.log.warning("Running with auth mocking enabled.")
        self.spawner = MockSpawner(parent=self)
        self.authenticator = AM(parent=self)
        self.app = falcon.API(
            middleware=[self.authenticator, RequireJSONMiddleware()]
        )
        ver = Version()
        ll = List(parent=self)
        single = SingleWorkflow(parent=self)
        pods = Pods(parent=self)
        logs = Logs(parent=self)
        new = New(parent=self)
        details = Details(parent=self)
        self.workflows = {}
        self.app.add_route("/", ll)
        self.app.add_route("/workflow", ll)
        self.app.add_route("/workflow/", ll)
        self.app.add_route("/workflows", ll)
        self.app.add_route("/workflows/", ll)
        self.app.add_route("/version", ver)
        self.app.add_route("/version/", ver)
        self.app.add_route("/new", new)
        self.app.add_route("/new/", new)
        self.app.add_route("/workflow/{wf_id}", single)
        self.app.add_route("/workflow/{wf_id}/pods", pods)
        self.app.add_route("/workflow/{wf_id}/logs", logs)
        self.app.add_route("/workflow/{wf_id}/details/{pod_id}", details)
