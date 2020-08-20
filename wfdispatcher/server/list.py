from eliot import log_call
from rubin_jupyter_utils.hub import LoggableChild
from ..objects.workflowmanager import RubinWorkflowManager


class List(LoggableChild):
    @log_call
    def on_get(self, req, resp):
        rm = RubinWorkflowManager(req=req)
        wfs = rm.list_workflows()
        if not wfs:
            resp.media = []
            return
        resp.media = extract_wf_names(wfs.items)


def extract_wf_names(wfl):
    rl = []
    for wf in wfl:
        rl.append({"name": wf.metadata.name})
    return rl
