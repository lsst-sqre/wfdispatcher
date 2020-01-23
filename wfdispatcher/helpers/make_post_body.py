import json


def make_post_body():
    data = {
        "type": "cmd",
        "command": ["/bin/echo", "Hello, world!"],
        "image": "lsstsqre/sciplat-lab:w_2020_01",
        "size": "tiny"
    }
    return json.dumps(data)
