from eliot import log_call
from rubin_jupyter_utils.hub import LoggableChild
from ..objects.workflowmanager import RubinWorkflowManager


class Logs(LoggableChild):
    @log_call
    def on_get(self, req, resp, wf_id):
        self.log.debug("Fetching logs for workflow '{}'".format(wf_id))
        rm = RubinWorkflowManager(req=req)
        resp.media = rm.get_logs(wf_id)
