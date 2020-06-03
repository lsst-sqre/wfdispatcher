from eliot import log_call
from jupyterhubutils import LoggableChild
from ..objects.workflowmanager import LSSTWorkflowManager


class Logs(LoggableChild):

    @log_call
    def on_get(self, req, resp, wf_id):
        self.log.debug("Fetching logs for workflow '{}'".format(wf_id))
        wm = LSSTWorkflowManager(req=req)
        resp.media = wm.get_logs(wf_id)
