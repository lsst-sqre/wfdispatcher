import argo
import json
import os
from argo.workflows.client import V1alpha1Api
from argo.workflows.config import load_kube_config, load_incluster_config
from kubernetes.config.config_exception import ConfigException
from argo.workflows.sdk import Workflow, template
# This is just a K8s V1Container.
from argo.workflows.sdk.templates import V1Container
from eliot import start_action
from kubernetes.client import V1ResourceRequirements, V1SecurityContext
from kubernetes.client.rest import ApiException
from kubernetes import client
from jupyterhubutils import Loggable, LSSTMiddleManager, LSSTConfig
from jupyterhubutils.utils import list_digest, str_true, assemble_gids
from ..helpers.extract_user_from_req import extract_user_from_req
from ..spawner.spawner import MockSpawner


class LSSTWorkflowManager(Loggable):
    '''This class contains LSST (er, Rubin Observatory)- specific logic
    regarding management of Argo Workflows.  it must be initialized with
    a Request (from the requests module), whose authentication header
    (usually 'X-Portal-Authorization') contains a JWT with claims that
    specify the user (in username_claim_field, usually 'uid') used to make
    the Workflow request.

    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cmd_vol = None
        self.cmd_mt = None
        self.workflow = None
        self.cfg_map = None
        self.wf_input = None
        self.user = None
        req = kwargs.pop('req', None)
        if not req:
            raise RuntimeError("'req' parameter must be provided!")
        auth_header_name = kwargs.pop('auth_header_name',
                                      'X-Portal-Authorization')
        username_claim_field = kwargs.pop('username_claim_field', 'uid')
        self.user = extract_user_from_req(
            req, auth_header_name, username_claim_field)
        if not self.user:
            raise RuntimeError("Could not determine user from request!")
        try:
            load_incluster_config()
            argo.workflows.config.load_incluster_config()
        except ConfigException:
            self.log.warning("In-cluster config failed! Falling back.")
            try:
                load_kube_config()
                argo.workflows.config.load_kube_config()
            except (ValueError, TypeError) as exc:
                self.log.error("Still errored: {}".format(exc))
                raise
        self.api = V1alpha1Api()
        self.coreapi = client.CoreV1Api()

    def define_configmap(self, data):
        '''This returns a k8s configmap using the data from the new-workflow
        POST.
        '''
        with start_action(action_type="define_configmap"):
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
                mount_path=("/opt/lsst/software/jupyterlab/" +
                            "noninteractive/command/"),
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
        with start_action(action_type="define_workflow"):
            wf_input = {}
            # FIXME Right now we can assume data is of type 'cmd'; we need
            # a little tweaking for 'nb' in that the command will be fixed
            # and the execution parameters will differ.
            lm = LSSTMiddleManager(parent=self, config=LSSTConfig())
            cfg = lm.config
            em = lm.env_mgr
            vm = lm.volume_mgr
            om = lm.optionsform_mgr
            # We use the user we created from the request that created the
            #  Workflow Manager.
            username = self.user.name
            uid = self.user.uid
            gids = assemble_gids(self.user.claims["isMemberOf"])
            em.create_pod_env()
            em_env = em.get_env()
            size_map = om.sizemap.get(data['size'])
            if not size_map:
                # Use default size
                self.log.warn("Options Form Manager had no sizemap!")
                cpu = cfg.tiny_cpu_max * (2 ** cfg.size_index)
                mem = cfg.mb_per_cpu * cpu
                cpu_guar = cpu / (float(cfg.lab_size_range))
                mem_guar = cfg.mb_per_cpu * cpu_guar
                size_map = {
                    "cpu": str(cpu),
                    "mem": "{}M".format(mem),
                    "cpu_guar": str(cpu_guar),
                    "mem_guar": "{}M".format(mem_guar)
                }
            self.log.debug(
                "Size '{}' resolves to '{}'".format(data['size'], size_map))
            ml = size_map['mem']
            cl = size_map['cpu']
            mg = size_map['mem_guar']
            cg = size_map['cpu_guar']
            # If we actually have this in the environment, use it
            # (Dask requires due to our configuration).  If we do not,
            # then make up something plausible, but it really doesn't
            # matter if we get it right, because it's not like we're
            # using the Dask proxy dashboard from inside a Workflow anyway.
            synth_jsp = '/nb/user/{}'.format(username)
            jsp = os.getenv('JUPYTERHUB_SERVER_PREFIX', synth_jsp)
            wf_input['mem_limit'] = ml
            wf_input['mem_guar'] = mg
            wf_input['cpu_limit'] = str(cl)
            wf_input['cpu_guar'] = str(cg)
            wf_input['image'] = data['image']
            wf_input['enable_multus'] = cfg.enable_multus
            env = {}
            vols = []
            vmts = []
            env.update(em_env)
            vm.make_volumes_from_config()
            vols.extend(vm.k8s_volumes)
            vmts.extend(vm.k8s_vol_mts)
            self.define_configmap(data)
            vols.append(self.cmd_vol)
            vmts.append(self.cmd_mt)
            env['DASK_VOLUME_B64'] = vm.get_dask_volume_b64()
            cname = "wf-{}-{}-{}".format(
                username,
                data['image'].split(':')[-1].replace('_', '-'),
                data['command'][0].split('/')[-1].replace('_', '-'))
            wf_input['name'] = cname
            env['MEM_LIMIT'] = ml
            env['MEM_GUARANTEE'] = mg
            env['CPU_LIMIT'] = str(cl)
            env['CPU_GUARANTEE'] = str(cg)
            env['JUPYTERHUB_USER'] = username
            env['NONINTERACTIVE'] = "TRUE"
            env['EXTERNAL_UID'] = str(uid)
            env['EXTERNAL_GROUPS'] = gids
            env['JUPYTERHUB_SERVER_PREFIX'] = jsp
            env['DEBUG'] = str_true(cfg.debug)
            env['ACCESS_TOKEN'] = self.user.access_token
            e_l = self._d2l(env)
            wf_input['env'] = e_l
            wf_input['username'] = username
            # Volumes and mounts aren't JSON-serializable...
            wf_input['vols'] = '{}'.format(vols)
            wf_input['vmts'] = '{}'.format(vmts)
            self.wf_input = wf_input
            self.log.debug("Input to Workflow Manipulator: {}".format(
                json.dumps(wf_input, indent=4, sort_keys=True)))
            # ...now put the real values back
            wf_input['vols'] = vols
            wf_input['vmts'] = vmts
            wf_input['command'] = data['command']
            self.wf_input = wf_input
            wf = LSSTWorkflow(parms=wf_input)
            self.log.debug("Workflow: {}".format(wf))
            self.workflow = wf

    def _d2l(self, in_d):
        with start_action(action_type="_d2l"):
            ll = []
            for k in in_d:
                ll.append({"name": k,
                           "value": in_d[k]})
            return ll

    def list_workflows(self):
        with start_action(action_type="list_workflows"):
            namespace = self.user.namespace
            self.log.debug(
                "Listing workflows in namespace '{}'".format(namespace))
            nl = self.coreapi.list_namespace(timeout_seconds=3)
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
                wfs = self.api.list_namespaced_workflows(namespace=namespace)
            return wfs

    def create_workflow(self):
        with start_action(action_type="create_workflows"):
            workflow = self.workflow
            namespace = self.user.namespace
            self.create_configmap()
            self.log.debug(
                "Creating workflow in namespace {}: '{}'".format(
                    namespace, workflow))
            wf = self.api.create_namespaced_workflow(namespace, workflow)
            return wf

    def create_configmap(self):
        with start_action(action_type="create_configmap"):
            api = self.coreapi  # Core, not Workflow
            namespace = self.user.namespace
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
        with start_action(action_type="submit_workflow"):
            self.define_workflow(data)
            user = self.user
            self.log.debug("submit_workflow user class: {}".format(
                user.__class__.__name__))
            self.log.debug(
                "submit_workflow username: {}".format(user.escaped_name))
            lm = LSSTMiddleManager(parent=self, config=LSSTConfig())
            lm.user = self.user  # Only works because JupyterHub Users and
            # our users both have escaped_name fields
            nm = lm.namespace_mgr
            nm.namespace = user.namespace
            lm.spawner = MockSpawner()
            nm.ensure_namespace()
            nm.ensure_namespaced_service_account()
            wf = self.create_workflow()
            return wf

    def delete_workflow(self, wfid):
        with start_action(action_type="delete_workflow"):
            namespace = self.user.namespace
            api = self.api
            wf = api.delete_namespaced_workflow(namespace, wfid)
            return wf

    def get_workflow(self, wfid):
        with start_action(action_type="get_workflow"):
            namespace = self.user.namespace
            api = self.api
            wf = api.get_namespaced_workflow(namespace, wfid)
            return wf

    def get_logs(self, wf_id):
        wf = self.get_workflow(wf_id)
        if not wf:
            self.log.debug("No workflow '{}' found".format(wf_id))
            return None
        namespace = self.user.namespace
        nd = wf.status.nodes
        loglist = []
        for pod_id in nd:
            self.log.debug("Getting logs for '{}' in namespace '{}'".format(
                pod_id, namespace))
            logs = self.coreapi.read_namespaced_pod_log(pod_id, namespace,
                                                        container='main')
            loglist.append({'name': pod_id,
                            'logs': logs})
        return loglist

    def dump(self):
        '''Return contents dict for aggregation and pretty-printing.
        '''
        wd = {
            "cmd_vol": str(self.cmd_vol),
            "workflow": str(self.workflow),
            "cfg_map": self.cfg_map,
            "wf_input": self.wf_input,
            "user": self.user.dump()
        }
        return wd

    def toJSON(self):
        return json.dumps(self.dump())


class LSSTWorkflow(Workflow):
    '''Class to represent LSST Workflow.
    '''

    entrypoint = "noninteractive"  # Actually a class variable.
    # see https://pypi.org/project/argo-workflows-sdk/

    def __init__(self, *args, **kwargs):
        self.parms = kwargs.pop('parms', {})
        self.run_as_user = kwargs.pop('run_as_user', 769)
        self.run_as_group = kwargs.pop('run_as_group', 769)
        super().__init__(*args, **kwargs)
        self.spec.volumes = self.parms['vols']
        lbl = {'argocd.argoproj.io/instance': 'nublado-users'}
        self.metadata.labels = lbl
        self.metadata.generate_name = self.parms['name'] + '-'
        self.metadata.name = None
        username = self.parms['username']
        account = "{}-svcacct".format(username)
        self.spec.service_account_name = account
        self.metadata.annotations = self.build_annotations()

    def build_annotations(self):
        '''Add annotations telling Argo CD to not prune these resources or to
        count them against the sync state.
        '''
        with start_action(action_type="build_annotations"):
            anno = {}
            anno['argocd.argoproj.io/compare-options'] = 'IgnoreExtraneous'
            anno['argocd.argoproj.io/sync-options'] = 'Prune=false'

            # Enable multus if requested
            if self.parms['enable_multus']:
                ks = 'kube-system/macvlan-conf'
                # This probably ought to be a config parameter
                anno['k8s.v1.cni.cncf.io/networks'] = ks

            cmdlist = self.parms['command']
            if not cmdlist:
                return anno
            annobase = "lsst.org/wf_cmd"
            idx = 0
            for cmd in cmdlist:
                akey = annobase + "_{}".format(idx)
                if len(cmd) < 64:
                    anno[akey] = cmd
                else:
                    jdx = 0
                    while cmd:
                        chunk = cmd[:63]
                        cmd = cmd[63:]
                        skey = akey + "_{}".format(jdx)
                        anno[skey] = chunk
                        jdx = jdx+1
                    idx = idx + 1
            return anno

    @template
    def noninteractive(self) -> V1Container:
        with start_action(action_type="noninteractive_container"):
            container = V1Container(
                command=["/opt/lsst/software/jupyterlab/provisionator.bash"],
                args=[],
                image=self.parms["image"],
                name=self.parms["name"],
                env=self.parms["env"],
                image_pull_policy="Always",
                volume_mounts=self.parms["vmts"],
                resources=V1ResourceRequirements(
                    limits={"memory": self.parms['mem_limit'],
                            "cpu": self.parms['cpu_limit']},
                    requests={"memory": self.parms['mem_guar'],
                              "cpu": self.parms['cpu_guar']}
                ),
                security_context=V1SecurityContext(
                    run_as_group=self.run_as_group,
                    run_as_user=self.run_as_user,
                )
            )
            self.volumes = self.parms['vols']
            lbl = {'argocd.argoproj.io/instance': 'nublado-users'}
            self.metadata.labels = lbl
            self.metadata.generate_name = self.parms['name'] + '-'
            self.metadata.name = None
            self.service_account_name = self.parms['username'] + '-svcacct'

            return container
