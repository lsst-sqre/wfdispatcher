from eliot import log_call
from falcon import HTTPNotFound
from rubin_jupyter_utils.hub import LoggableChild
from ..helpers.sanitize import sanitize
from ..objects.workflowmanager import RubinWorkflowManager


class SingleWorkflow(LoggableChild):
    @log_call
    def on_get(self, req, resp, wf_id):
        self.log.debug("Getting workflow '{}'".format(wf_id))
        rm = RubinWorkflowManager(req=req)
        wf = rm.get_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        resp.media = sanitize(wf)

    @log_call
    def on_delete(self, req, resp, wf_id):
        self.log.debug("Deleting workflow '{}'".format(wf_id))
        rm = RubinWorkflowManager(req=req)
        wf = rm.delete_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        status = wf["status"]
        rv = {"status": status}
        if status == "Success":
            rv["name"] = wf["details"]["name"]
        resp.media = rv
