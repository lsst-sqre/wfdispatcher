import hashlib


def list_digest(inp_list):
    if type(inp_list) is not list:
        raise TypeError("list_digest only works on lists!")
    if not inp_list:
        raise ValueError("input must be a non-empty list!")
    # If we can rely on python >= 3.8, shlex.join is better
    return hashlib.sha256(' '.join(inp_list).encode('utf-8')).hexdigest()
