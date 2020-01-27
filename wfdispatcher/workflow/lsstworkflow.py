from argo.workflows.sdk import Workflow, template
from argo.workflows.sdk.templates import V1Container
from kubernetes.client import V1ResourceRequirements, V1SecurityContext
# This is just a K8s V1Container.


class LSSTWorkflow(Workflow):
    parms = {}
    entrypoint = "noninteractive"

    def __init__(self, *args, **kwargs):
        self.parms = kwargs.pop('parms')
        super().__init__(*args, **kwargs)
        self.spec.volumes = self.parms['vols']
        lbl = {'argocd.argoproj.io/instance': 'nublado-users'}
        self.metadata.labels = lbl
        self.metadata.generate_name = self.parms['name'] + '-'
        self.metadata.name = None

    @template
    def noninteractive(self) -> V1Container:
        container = V1Container(
            command=["/opt/lsst/software/jupyterlab/provisionator.bash"],
            args=[],
            image=self.parms["image"],
            name=self.parms["name"],
            env=self.parms["env"],
            image_pull_policy="Always",
            volume_mounts=self.parms["vmts"],
            resources=V1ResourceRequirements(
                limits={"memory": "{}M".format(self.parms['mem_limit']),
                        "cpu": "{}".format(self.parms['cpu_limit'])},
                requests={"memory": "{}M".format(self.parms['mem_guar']),
                          "cpu": "{}".format(self.parms['cpu_guar'])}),
            security_context=V1SecurityContext(
                run_as_group=769,
                run_as_user=769,
            )
        )
        self.volumes = self.parms['vols']
        lbl = {'argocd.argoproj.io/instance': 'nublado-users'}
        self.metadata.labels = lbl
        self.metadata.generate_name = self.parms['name'] + '-'
        self.metadata.name = None

        return container
