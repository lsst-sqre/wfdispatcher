import json
import falcon
from jupyterhubutils import LoggableChild
from .list import extract_wf_names


class New(LoggableChild):

    def on_post(self, req, resp):
        '''Handle the request to create a new Workflow.
        The POST body will be JSON-encoded (enforced by Falcon middleware)

        The body structure must look like:
        {
          type: <lsp workflow type, either 'nb' or 'cmd',
          kernel:  <only relevant with type nb: kernel name, e.g. 'LSST'>,
          command: [ <list of tokens to assemble to make a command line;
                      quoting rules are the same as python's shlex;
                      only relevant with type cmd> ],

          image: <nublado image str, e.g. 'lsstsqre/sciplat-lab:w_2020_01'>,
          size: <str from form_sizelist in LSSTConfig>
        }

        The first three parameters will be passed in to the spawned
        container as a json file, specified in a configmap and mounted at
        /opt/lsst/software/jupyterlab/noninteractive/command/command.json .

        The last two will be used to create the container itself.
        '''
        data = req.media
        self.log.debug("Received POST body: {}".format(
            json.dumps(data, sort_keys=True, indent=4)))
        self._validate_input(data)
        # If we got here, it's syntactically valid
        wf_name = self.make_workflow(data)
        resp.media = {"name": wf_name}

    def _validate_input(self, data):
        '''Raises an exception if the posted data does not conform to
        expectations.
        '''
        typ = data.get('type')
        ue = falcon.HTTPUnprocessableEntity
        allowable_types = ['nb', 'cmd']
        if typ not in allowable_types:
            raise ue(
                description="'{}' not one of '{}'!".format(
                    type, allowable_types))
        if typ == 'nb':
            raise ue("Execution type 'nb' not yet supported!")
            # We do not get here, but once we do....
            kernel = type.get("kernel")
            if type(kernel) is not str:
                raise ue(description="'kernel' must be a string!")
            if not kernel:
                raise ue(description="No kernel specified for notebook!")
        elif typ == 'cmd':
            cmd = data.get("command")
            if type(cmd) is not list:
                raise ue(description="'cmd' must be a list!")
            if not cmd:
                raise ue(description="No command specified!")
        else:
            # This should be unreachable, and if you get here it means
            #  someone added a new type to allowable_types, but didn't update
            #  the if statement we're in.
            raise ue(description="Unknown type '{}'!".format(typ))
        image = data.get('image')
        if type(image) is not str:
            raise ue(description="'image' must be a string!")
        if not image:
            raise ue("No image specified for container!")
        sz = data.get('size')
        szl = self.parent.lsst_mgr.config.form_sizelist
        if type(sz) is not str or sz not in szl:
            raise ue(
                description="'size' must be a string from '{}'!".format(szl))

    def make_workflow(self, data):
        wm = self.parent.lsst_mgr.workflow_mgr
        # There might be no namespace at all, in which case, list_workflows
        #  returns None
        owf = wm.list_workflows()
        origlist = []
        if owf:
            origlist = [x['name']
                        for x in extract_wf_names(owf.items)]
        wf = wm.submit_workflow(data)
        pref = wm.wf_input['name'] + '-'
        newlist = [x['name']
                   for x in extract_wf_names(wm.list_workflows().items)]
        for n in newlist:
            if n.startswith(pref) and n not in origlist:
                return n
