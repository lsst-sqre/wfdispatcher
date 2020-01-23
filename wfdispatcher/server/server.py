'''Simple RESTful API server for dispatching Argo Workflows.
'''

import falcon
from ..auth.auth import Authenticator
from .requirejson import RequireJSON
from .new import New
from .list import List
from .singleworkflow import SingleWorkflow
from .version import Version
from jupyterhubutils import make_logger, LSSTConfig, LSSTMiddleManager
from ..workflow.workflowmanager import LSSTWorkflowManager


class Server(object):
    config = None
    verify_signature = True
    verify_audience = True
    auth = None
    app = None
    _mock = False

    def __init__(self, *args, **kwargs):
        self.lsst_mgr = LSSTMiddleManager(parent=self, config=LSSTConfig())
        self.log = make_logger()
        self.log.debug("Creating WorkflowAPIServer")
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

        self.auth = Authenticator(parent=self, _mock=_mock,
                                  verify_signature=verify_signature,
                                  verify_audience=verify_audience)
        self.lsst_mgr.optionsform_mgr._make_sizemap()
        self.lsst_mgr.workflow_mgr = LSSTWorkflowManager(
            parent=self.lsst_mgr)
        self.app = falcon.API(middleware=[
            self.auth,
            RequireJSON()
        ])
        ver = Version()
        ll = List(parent=self)
        single = SingleWorkflow(parent=self)
        self.app.add_route('/', ll)
        self.app.add_route('/workflows', ll)
        self.app.add_route('/version', ver)
        self.app.add_route('/new', New(parent=self))
        self.app.add_route('/workflow/{wf_id}', single)
