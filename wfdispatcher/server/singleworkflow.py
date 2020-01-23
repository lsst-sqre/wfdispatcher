from ..loggablechild import LoggableChild


class SingleWorkflow(LoggableChild):

    def on_get(self, req, resp, wf_id):
        wf = self.parent.lsst_mgr.workflow_mgr.get_workflow(wf_id)
        self.log.debug("Received response: '{}'".format(wf))
        # Transform somehow and return in resp.

    def on_delete(self, req, resp, wf_id):
        wf = self.parent.lsst_mgr.workflow_mgr.delete_workflow(wf_id)
        self.log.debug("Received response: '{}'".format(wf))
        # Transform somehow and return in resp.
