import os


def get_default_namespace():
    """
    Set namespace default to current namespace if running in a k8s cluster

    If not in a k8s cluster with service accounts enabled, default to
    `default`

    Stolen from jupyterhub/kubespawner's _namespace_default
    """
    ns_path = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    if os.path.exists(ns_path):
        with open(ns_path) as f:
            return f.read().strip()
    return 'default'
