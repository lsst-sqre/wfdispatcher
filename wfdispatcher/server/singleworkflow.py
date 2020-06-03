from argo.workflows.sdk._utils import sanitize_for_serialization
from eliot import log_call
from falcon import HTTPNotFound
from jupyterhubutils import LoggableChild
from ..objects.workflowmanager import LSSTWorkflowManager


class SingleWorkflow(LoggableChild):

    @log_call
    def on_get(self, req, resp, wf_id):
        self.log.debug("Getting workflow '{}'".format(wf_id))
        wm = LSSTWorkflowManager(req=req)
        wf = wm.get_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        resp.media = sanitize_for_serialization(wf)

    @log_call
    def on_delete(self, req, resp, wf_id):
        self.log.debug("Deleting workflow '{}'".format(wf_id))
        wm = LSSTWorkflowManager(req=req)
        wf = wm.delete_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        status = wf['status']
        rv = {"status": status}
        if status == "Success":
            rv['name'] = wf['details']['name']
        resp.media = rv
