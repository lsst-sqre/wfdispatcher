from eliot import log_call
from jupyterhubutils import LoggableChild
from ..objects.workflowmanager import LSSTWorkflowManager


class List(LoggableChild):

    @log_call
    def on_get(self, req, resp):
        wm = LSSTWorkflowManager(req=req)
        wfs = wm.list_workflows()
        if not wfs:
            resp.media = []
            return
        resp.media = extract_wf_names(wfs.items)


def extract_wf_names(wfl):
    rl = []
    for wf in wfl:
        rl.append({"name": wf.metadata.name})
    return rl
