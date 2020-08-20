from argo.workflows.client import ApiClient


def sanitize(obj):
    """Return an object suitable for a JSON post.
    """
    cl = ApiClient()
    try:
        return cl.sanitize_for_serialization(obj)
    except AttributeError:
        # This catches
        # AttributeError: 'V1Container' object has no attribute 'swagger_types'
        d_obj = obj.to_dict()
        return cl.sanitize_for_serialization(d_obj)
