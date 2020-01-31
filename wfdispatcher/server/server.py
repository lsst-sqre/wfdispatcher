'''Simple RESTful API server for dispatching Argo Workflows.
'''

import falcon
from ..auth.auth import AuthenticatorMiddleware
from ..helpers.mockspawner import MockSpawner
from .requirejson import RequireJSONMiddleware
from .new import New
from .details import Details
from .list import List
from .logs import Logs
from .pods import Pods
from .singleworkflow import SingleWorkflow
from .version import Version
from jupyterhubutils import Loggable, LSSTConfig, LSSTMiddleManager


class Server(Loggable):
    config = None
    verify_signature = True
    verify_audience = True
    auth = None
    app = None
    lsst_mgr = None
    spawner = None
    _mock = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lsst_mgr = LSSTMiddleManager(parent=self, config=LSSTConfig())
        _mock = kwargs.pop('_mock', self._mock)
        self._mock = _mock
        if _mock:
            self.log.warning("Running with auth mocking enabled.")
        verify_signature = kwargs.pop('verify_signature',
                                      self.verify_signature)
        self.verify_signature = verify_signature
        if not verify_signature:
            self.log.warning("Running with signature verification disabled.")
        verify_audience = kwargs.pop('verify_audience',
                                     self.verify_audience)
        self.verify_audience = verify_audience
        if not verify_audience:
            self.log.warning("Running with audience verification disabled.")
        self.auth = AuthenticatorMiddleware(parent=self, _mock=_mock,
                                            verify_signature=verify_signature,
                                            verify_audience=verify_audience)
        self.spawner = MockSpawner(parent=self)
        self.lsst_mgr.optionsform_mgr._make_sizemap()
        self.lsst_mgr.spawner = self.spawner
        self.lsst_mgr.volume_mgr.make_volumes_from_config()
        self.app = falcon.API(middleware=[
            self.auth,
            RequireJSONMiddleware()
        ])
        ver = Version()
        ll = List(parent=self)
        single = SingleWorkflow(parent=self)
        pods = Pods(parent=self)
        logs = Logs(parent=self)
        new = New(parent=self)
        details = Details(parent=self)
        self.app.add_route('/', ll)
        self.app.add_route('/workflow', ll)
        self.app.add_route('/workflow/', ll)
        self.app.add_route('/workflows', ll)
        self.app.add_route('/workflows/', ll)
        self.app.add_route('/version', ver)
        self.app.add_route('/version/', ver)
        self.app.add_route('/new', new)
        self.app.add_route('/new/', new)
        self.app.add_route('/workflow/{wf_id}', single)
        self.app.add_route('/workflow/{wf_id}/pods', pods)
        self.app.add_route('/workflow/{wf_id}/logs', logs)
        self.app.add_route('/workflow/{wf_id}/details/{pod_id}', details)
