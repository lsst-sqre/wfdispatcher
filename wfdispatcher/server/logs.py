from jupyterhubutils import LoggableChild


class Logs(LoggableChild):

    def on_get(self, req, resp, wf_id):
        self.log.debug("Fetching logs for workflow '{}'".format(wf_id))
        lm = self.parent.lsst_mgr
        nm = lm.namespace_mgr
        namespace = nm.namespace
        wm = lm.workflow_mgr
        api = lm.api
        wf = wm.get_workflow(wf_id)
        if not wf:
            self.log.debug("No workflow '{}' found".format(wf_id))
            resp.media = None
            return
        nd = wf.status.nodes
        resp.media = []
        for pod_id in nd:
            self.log.debug("Getting logs for '{}' in namespace '{}'".format(
                pod_id, namespace))
            logs = api.read_namespaced_pod_log(pod_id, namespace,
                                               container='main')
            resp.media.append({'name': pod_id,
                               'logs': logs})
