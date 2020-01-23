from ..loggablechild import LoggableChild


class List(LoggableChild):

    def on_get(self, req, resp):
        username = self.parent.auth.user.name
        nsm = self.parent.lsst_mgr.namespace_mgr
        wfm = self.parent.lsst_mgr.workflow_mgr
        namespace = nsm.namespace
        self.log.debug(
            "Received list request for user '{}' in namespace '{}'".format(
                username, namespace))
        wfs = wfm.list_workflows()
        resp.media = wfs
