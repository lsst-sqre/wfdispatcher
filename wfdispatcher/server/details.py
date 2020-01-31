from jupyterhubutils import LoggableChild
from argo.workflows.sdk._utils import sanitize_for_serialization
from falcon import HTTPNotFound


class Details(LoggableChild):

    def on_get(self, req, resp, wf_id, pod_id):
        self.log.debug("Getting details for pod '{}' in workflow '{}'".format(
            pod_id, wf_id))
        lm = self.parent.lsst_mgr
        wm = lm.workflow_mgr
        wf = wm.get_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        nd = wf.status.nodes
        if not nd:
            raise HTTPNotFound()
        pod = nd.get(pod_id)
        if not pod:
            raise HTTPNotFound()
        resp.media = sanitize_for_serialization(pod)
