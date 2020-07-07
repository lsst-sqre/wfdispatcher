import json
import falcon
from eliot import log_call, start_action
from jupyterhubutils import LoggableChild, LSSTMiddleManager, LSSTConfig
from ..objects.workflowmanager import LSSTWorkflowManager


class New(LoggableChild):

    @log_call
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
          size: <str from form_sizelist in LSSTConfig>,
          no_sudo: <bool>,
          debug: <bool>
        }

        The first three parameters will be passed in to the spawned
        container as a json file, specified in a configmap and mounted at
        /opt/lsst/software/jupyterlab/noninteractive/command/command.json .

        The last four will be used to create the container itself.  The
        booleans default to False if omitted.
        '''
        data = req.media
        self.log.debug("Received POST body: {}".format(
            json.dumps(data, sort_keys=True, indent=4)))
        self._validate_input(data)
        # If we got here, it's syntactically valid
        wf = self.make_workflow(req, data)
        if wf:
            resp.media = {"name": wf.metadata.name}
        else:
            raise falcon.HTTPInternalServerError(
                description="No workflow created")

    @log_call
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
        lm = LSSTMiddleManager(parent=self, config=LSSTConfig())
        szl = lm.config.form_sizelist
        if type(sz) is not str or sz not in szl:
            raise ue(
                description="'size' must be a string from '{}'!".format(szl))

    def make_workflow(self, req, data):
        with start_action(action_type="make_workflow"):
            wm = LSSTWorkflowManager(req=req)
            wf = wm.submit_workflow(data)
            return wf
