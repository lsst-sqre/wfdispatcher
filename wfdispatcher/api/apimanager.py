from ..loggablechild import LoggableChild
from jupyterhubutils import Singleton
from kubernetes.client import CoreV1Api, RbacAuthorizationV1Api
from kubernetes.config import load_incluster_config, load_kube_config
from kubernetes.config.config_exception import ConfigException
from argo.workflows.client import V1alpha1Api
import argo.workflows.config


class LSSTAPIManager(LoggableChild, metaclass=Singleton):
    argo_api = None
    rbac_api = None
    api = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            load_incluster_config()
            argo.workflows.config.load_incluster_config()
        except ConfigException:
            self.log.warning("In-cluster config failed! Falling back.")
            try:
                load_kube_config()
                argo.workflows.config.load_kube_config()
            except ValueError as exc:
                self.log.error("Still errored: {}".format(exc))
        argo_api = kwargs.pop('argo_api', self.argo_api)
        if not argo_api:
            argo_api = V1alpha1Api()
        self.argo_api = argo_api
        rbac_api = kwargs.pop('rbac_api', self.rbac_api)
        if not rbac_api:
            rbac_api = RbacAuthorizationV1Api()
        self.rbac_api = rbac_api
        api = kwargs.pop('api', self.api)
        if not api:
            api = CoreV1Api()
        self.api = api
