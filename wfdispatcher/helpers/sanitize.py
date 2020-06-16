from argo.workflows.client import ApiClient


def sanitize(obj):
    cl = ApiClient()
    return cl.sanitize_for_serialization(obj)
