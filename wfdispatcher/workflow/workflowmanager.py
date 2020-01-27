import json
from argo.workflows.client import V1alpha1Api
from argo.workflows.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from kubernetes.client.rest import ApiException
from jupyterhubutils import str_true
from kubernetes import client
from .lsstworkflow import LSSTWorkflow
from ..loggablechild import LoggableChild
from ..util.list_digest import list_digest


class LSSTWorkflowManager(LoggableChild):
    '''This should perhaps eventually move into jupyterhubutils.
    It is an LSST Manager Class containing LSST (er, Rubin Observatory)-
    specific logic.
    '''

    cmd_vol = None
    cmd_mt = None
    argo_api = None
    workflow = None
    cfg_map = None
    wf_input = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argo_api = self._get_api()

    def _get_api(self):
        try:
            load_incluster_config()
        except ConfigException:
            self.log.warning("In-cluster config failed! Falling back.")
            try:
                load_kube_config()
            except ValueError as exc:
                self.log.error("Still errored: {}".format(exc))
        api = V1alpha1Api()
        return api

    def define_configmap(self, data):
        '''This returns a k8s configmap using the data from the new-workflow
        POST.
        '''
        ni_cmd = data['command']
        idkey = list_digest(ni_cmd)
        cm_name = 'command.{}.json'.format(idkey)
        k8s_vol = client.V1Volume(
            name="noninteractive-command",
            config_map=client.V1ConfigMapVolumeSource(
                name=cm_name
            ),
        )
        k8s_mt = client.V1VolumeMount(
            name="noninteractive-command",
            mount_path="/opt/lsst/software/jupyterlab/noninteractive/command/",
            read_only=True
        )
        self.cmd_vol = k8s_vol
        self.cmd_mt = k8s_mt
        # Now the configmap
        cm_data = {}
        cm_data.update(data)
        del cm_data['image']
        del cm_data['size']
        jd = json.dumps(data, sort_keys=True, indent=4)
        k8s_configmap = client.V1ConfigMap(
            metadata=client.V1ObjectMeta(name=cm_name),
            data={'command.json': json.dumps(data)})
        self.log.debug("Created configmap '{}': {}".format(cm_name, jd))
        self.cfg_map = k8s_configmap

    def define_workflow(self, data):
        '''This is basically our equivalent of get_pod_manifest().
        It creates a dict which we will pass to the workflow template
        engine, which will allow it to create an appropriate workflow.
        '''
        wf_input = {}
        # FIXME Right now we can assume data is of type 'cmd'; we need
        # a little tweaking for 'nb' in that the command will be fixed
        # and the execution parameters will differ.
        cfg = self.parent.config
        em = self.parent.env_mgr
        vm = self.parent.volume_mgr
        am = self.parent.auth_mgr
        user = self.parent.parent.auth.user
        em_env = em.get_env()
        size_map = self._resolve_size(data['size'])
        self.log.debug(
            "Size '{}' resolves to '{}'".format(data['size'], size_map))
        ml = size_map['mem']
        cl = size_map['cpu']
        sr = float(cfg.lab_size_range)
        mg = None
        cg = None
        if data['size'] == "tiny":
            # Take the guarantees from the config object
            mg = cfg.mem_guarantee
            mgs = str(mg)
            # I really screwed up these defaults.
            while mgs and not mgs[-1].isdigit():
                mgs = mgs[:-1]
            if not mgs:
                mgs = '1.0'
            mg = float(mgs)
            cg = cfg.cpu_guarantee
        else:
            mg = float(ml / sr)
            cg = float(cl / sr)
        mg = int(mg)
        ml = int(ml)
        wf_input['mem_limit'] = ml
        wf_input['mem_guar'] = mg
        wf_input['cpu_limit'] = cl
        wf_input['cpu_guar'] = cg
        wf_input['image'] = data['image']
        env = {}
        vols = []
        vmts = []
        env.update(em_env)
        vols.extend(vm.k8s_volumes)
        vmts.extend(vm.k8s_vol_mts)
        self.define_configmap(data)
        vols.append(self.cmd_vol)
        vmts.append(self.cmd_mt)
        env['DASK_VOLUME_B64'] = vm.get_dask_volume_b64()
        cname = "wf-{}-{}-{}".format(
            user.escaped_name,
            data['image'].split(':')[-1].replace('_', '-'),
            data['command'][0].split('/')[-1].replace('_', '-'))
        wf_input['name'] = cname
        env['JUPYTERHUB_USER'] = cname
        env['NONINTERACTIVE'] = "TRUE"
        env['EXTERNAL_UID'] = str(user.auth_state['uid'])
        env['EXTERNAL_GROUPS'] = am.get_group_string()
        env['DEBUG'] = str_true(cfg.debug)
        e_l = self._d2l(env)
        wf_input['env'] = e_l
        # Volumes and mounts aren't JSON-serializable...
        wf_input['vols'] = '{}'.format(vols)
        wf_input['vmts'] = '{}'.format(vmts)
        self.wf_input = wf_input
        self.log.debug("Input to Workflow Manipulator: {}".format(
            json.dumps(wf_input, indent=4, sort_keys=True)))
        # ...now put the real values back
        wf_input['vols'] = vols
        wf_input['vmts'] = vmts
        self.wf_input = wf_input

        wf = LSSTWorkflow(parms=wf_input)
        self.log.debug("Workflow: {}".format(wf))
        self.workflow = wf

    def _resolve_size(self, size):
        om = self.parent.optionsform_mgr
        return om.sizemap.get(size)

    def _d2l(self, in_d):
        ll = []
        for k in in_d:
            ll.append({"name": k,
                       "value": in_d[k]})
        return ll

    def list_workflows(self):
        namespace = self.parent.namespace_mgr.namespace
        api = self.argo_api
        self.log.debug(
            "Listing workflows in namespace '{}'".format(namespace))
        nl = self.parent.api.list_namespace(timeout_seconds=1)
        found = False
        for ns in nl.items:
            nsname = ns.metadata.name
            if nsname == namespace:
                self.log.debug("Namespace {} found.".format(namespace))
                found = True
                break
        if not found:
            self.log.debug("No namespace {} found.".format(namespace))
            wfs = None
        else:
            wfs = api.list_namespaced_workflows(namespace=namespace)
        return wfs

    def create_workflow(self):
        workflow = self.workflow
        namespace = self.parent.namespace_mgr.namespace
        api = self.argo_api
        self.create_configmap()
        self.log.debug(
            "Creating workflow in namespace {}: '{}'".format(
                namespace, workflow))
        wf = api.create_namespaced_workflow(namespace, workflow)
        return wf

    def create_configmap(self):
        api = self.parent.api
        namespace = self.parent.namespace_mgr.namespace
        cfgmap = self.cfg_map
        try:
            self.log.info(
                "Attempting to create configmap in {}".format(namespace))
            api.create_namespaced_config_map(namespace, cfgmap)
        except ApiException as e:
            if e.status != 409:
                estr = "Create configmap failed: {}".format(e)
                self.log.exception(estr)
                raise
            else:
                self.log.info("Configmap already exists.")

    def submit_workflow(self, data):
        self.define_workflow(data)
        nm = self.parent.namespace_mgr
        nm.ensure_namespace()
        self._ensure_namespaced_account_objects()
        self.create_workflow()

    def _ensure_namespaced_account_objects(self):
        # Create a service account with role and rolebinding to allow it
        #  to manipulate pods in the namespace.
        self.log.info("Ensuring namespaced service account.")
        namespace = self.parent.namespace_mgr.namespace
        api = self.parent.api
        rbac_api = self.parent.rbac_api
        svcacct, role, rolebinding = self._define_namespaced_account_objects()
        account = self.service_account
        try:
            self.log.info("Attempting to create service account.")
            api.create_namespaced_service_account(
                namespace=namespace,
                body=svcacct)
        except ApiException as e:
            if e.status != 409:
                self.log.exception("Create service account '%s' " % account +
                                   "in namespace '%s' " % namespace +
                                   "failed: %s" % str(e))
                raise
            else:
                self.log.info("Service account '%s' " % account +
                              "in namespace '%s' already exists." % namespace)
        try:
            self.log.info("Attempting to create role in namespace.")
            rbac_api.create_namespaced_role(
                namespace,
                role)
        except ApiException as e:
            if e.status != 409:
                self.log.exception("Create role '%s' " % account +
                                   "in namespace '%s' " % namespace +
                                   "failed: %s" % str(e))
                raise
            else:
                self.log.info("Role '%s' " % account +
                              "already exists in namespace '%s'." % namespace)
        try:
            self.log.info("Attempting to create rolebinding in namespace.")
            rbac_api.create_namespaced_role_binding(
                namespace,
                rolebinding)
        except ApiException as e:
            if e.status != 409:
                self.log.exception("Create rolebinding '%s'" % account +
                                   "in namespace '%s' " % namespace +
                                   "failed: %s", str(e))
                raise
            else:
                self.log.info("Rolebinding '%s' " % account +
                              "already exists in '%s'." % namespace)

    def _define_namespaced_account_objects(self):
        namespace = self.parent.namespace_mgr.namespace
        username = self.parent.parent.auth.user.escaped_name
        account = "{}-{}".format(username, "argo")
        self.service_account = account
        md = client.V1ObjectMeta(
            name=account,
            labels={'argocd.argoproj.io/instance': 'nublado-users'})
        svcacct = client.V1ServiceAccount(metadata=md)
        rules = [
            client.V1PolicyRule(
                api_groups=["argoproj.io"],
                resources=["workflows", "workflows/finalizers"],
                verbs=["get", "list", "watch", "update", "patch", "delete"]
            ),
            client.V1PolicyRule(
                api_groups=["argoproj.io"],
                resources=["workflowtemplates",
                           "workflowtemplates/finalizers"],
                verbs=["get", "list", "watch"],
            ),

            client.V1PolicyRule(
                api_groups=[""],
                resources=["secrets"],
                verbs=["get"]
            ),
            client.V1PolicyRule(
                api_groups=[""],
                resources=["configmaps"],
                verbs=["list"]
            ),
            client.V1PolicyRule(
                api_groups=[""],
                resources=["pods", "services"],
                verbs=["get", "list", "watch", "create", "delete"]
            ),
            client.V1PolicyRule(
                api_groups=[""],
                resources=["pods/log", "serviceaccounts"],
                verbs=["get", "list"]
            ),
        ]
        role = client.V1Role(
            rules=rules,
            metadata=md)
        rolebinding = client.V1RoleBinding(
            metadata=md,
            role_ref=client.V1RoleRef(api_group="rbac.authorization.k8s.io",
                                      kind="Role",
                                      name=account),
            subjects=[client.V1Subject(
                kind="ServiceAccount",
                name=account,
                namespace=namespace)]
        )
        return svcacct, role, rolebinding

    def delete_workflow(self, wfid):
        namespace = self.parent.namespace_mgr.namespace
        api = self.argo_api
        wf = api.delete_namespaced_workflow(namespace, wfid)
        return wf

    def get_workflow(self, wfid):
        namespace = self.parent.namespace_mgr.namespace
        api = self.argo_api
        wf = api.get_namespaced_workflow(namespace, wfid)
        return wf
