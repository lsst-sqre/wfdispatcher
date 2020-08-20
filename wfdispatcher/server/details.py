from rubin_jupyter_utils.hub import LoggableChild
from eliot import log_call
from falcon import HTTPNotFound
from ..helpers.sanitize import sanitize
from ..objects.workflowmanager import RubinWorkflowManager


class Details(LoggableChild):
    @log_call
    def on_get(self, req, resp, wf_id, pod_id):
        self.log.debug(
            "Getting details for pod '{}' in workflow '{}'".format(
                pod_id, wf_id
            )
        )
        rm = RubinWorkflowManager(req=req)
        wf = rm.get_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        nd = wf.status.nodes
        if not nd:
            raise HTTPNotFound()
        pod = nd.get(pod_id)
        if not pod:
            raise HTTPNotFound()
        resp.media = sanitize(pod)
