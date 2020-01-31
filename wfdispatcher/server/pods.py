from jupyterhubutils import LoggableChild
from falcon import HTTPNotFound


class Pods(LoggableChild):

    def on_get(self, req, resp, wf_id):
        self.log.debug("Determining pods in workflow '{}'".format(wf_id))
        wf = self.parent.lsst_mgr.workflow_mgr.get_workflow(wf_id)
        if not wf:
            raise HTTPNotFound()
        nd = wf.status.nodes
        if not nd:
            raise HTTPNotFound()
        rv = []
        for k in nd:
            rv.append({"name": k})
        resp.media = rv
