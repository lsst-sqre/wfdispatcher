from argo.workflows.sdk import Workflow, template
from argo.workflows.sdk.templates import V1Container
# This is just a K8s V1Container.


class LSSTWorkflow(Workflow):
    parms = {}
    entrypoint = "noninteractive"

    def __init__(self, *args, **kwargs):
        self.parms = kwargs.pop('parms')
        super().__init__(*args, **kwargs)

    @template
    def noninteractive(self) -> V1Container:
        container = V1Container(
            image=self.parms["image"],
            name=self.parms["name"],
            env=self.parms["env"],
            image_pull_policy="always",
            volume_mounts=self.parms["vmts"]
        )
        self.spec.volumes = self.parms["vols"]
        lbl = {'argocd.argoproj.io/instance': 'nublado-users'}
        self.metadata.labels = lbl
        return container
