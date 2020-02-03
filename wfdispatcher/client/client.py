import json
import os
import requests
from json.decoder import JSONDecodeError
from jupyterhubutils import Loggable


class Client(Loggable):
    access_token = None
    auth_header_name = 'X-Portal-Authorization'
    env_var_name = 'ACCESS_TOKEN'
    api_url = "http://localhost:8080/"
    headers = {}
    last_response = None
    data = None
    post_json_file = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        auth_header_name = kwargs.pop(
            'auth_header_name', self.auth_header_name)
        self.auth_header_name = auth_header_name
        env_var_name = kwargs.pop('env_var_name', self.env_var_name)
        self.env_var_name = env_var_name
        access_token = kwargs.pop('access_token', self.access_token)
        if not access_token:
            access_token = os.getenv(env_var_name)
        if not access_token:
            raise EnvironmentError("{} is not set!".format(self.env_var_name))
        self.access_token = access_token
        self.make_headers()
        api_url = kwargs.pop('api_url', self.api_url)
        self.api_url = api_url
        # Canonicalize
        if not self.api_url.endswith('/'):
            self.api_url = "{}/".format(self.api_url)
        data = kwargs.pop('data', self.data)
        self.data = data
        post_json_file = kwargs.pop('post_json_file', self.post_json_file)
        self.post_json_file = post_json_file
        if not self.data and self.post_json_file:
            self.load_data()

    def make_headers(self):
        self.headers = {"{}".format(self.auth_header_name): "bearer {}".format(
            self.access_token),
            "Content-Type": "application/json"}

    def make_request(self, path=None, verb="GET"):
        verb = verb.upper()
        data = self.data
        if path is None:
            path = ""
        if verb == "POST":
            if data is None:
                raise ValueError("Data for POST cannot be None!")
        else:
            data = None
        url = "{}{}".format(self.api_url, path)
        dstr = "Making request {} {} ".format(verb, url)
        h_copy = {}
        h_copy.update(self.headers)
        if h_copy.get(self.auth_header_name):
            h_copy[self.auth_header_name] = "bearer [REDACTED]"
        dstr += "with headers {}".format(h_copy)
        if data:
            dstr += " and data '{}'".format(json.dumps(data, sort_keys=True,
                                                       indent=4))
        self.log.debug(dstr)
        response = requests.request(
            verb, url, headers=self.headers, json=data)
        try:
            jr = response.json()
            self.last_response = jr
        except JSONDecodeError as exc:
            self.log.error("{}: JSON decode failed".format(exc))
            self.log.error("Response was: {}".format(response.text))
            self.last_response = None

    def load_data(self):
        with open(self.post_json_file, 'r') as f:
            self.data = json.load(f)
        self.log.debug("Loaded data: {}".format(self.data))

    def list(self):
        self.make_request()

    def new(self):
        self.make_request(verb="POST", path="new")

    def version(self):
        self.make_request(path="version")

    def delete(self, wf_id):
        self.make_request(verb="DELETE", path="workflow/{}".format(wf_id))

    def inspect(self, wf_id):
        self.make_request(path="workflow/{}".format(wf_id))

    def logs(self, wf_id):
        self.make_request(path="workflow/{}/logs".format(wf_id))

    def pods(self, wf_id):
        self.make_request(path="workflow/{}/pods".format(wf_id))

    def details(self, wf_id, pod_id):
        self.make_request(path="workflow/{}/details/{}".format(wf_id, pod_id))

    def show_response(self):
        print(json.dumps(self.last_response, sort_keys=True, indent=4))
