import falcon
from eliot import log_call, start_action
from jupyterhubutils import LoggableChild
from jupyterhubutils.utils import get_execution_namespace, parse_access_token
from urllib.parse import quote
from ..helpers.make_mock_user import make_mock_user
from ..user.user import User


def get_default_namespace():
    ns = get_execution_namespace()
    if ns is None:
        ns = "default"
    return ns


class AuthenticatorMiddleware(LoggableChild):

    def __init__(self, *args, **kwargs):
        self.parent = None
        self.token = None
        super().__init__(*args, **kwargs)  # Sets self.parent
        self.log.debug("Creating Authenticator.")
        self._mock = kwargs.pop('_mock', False)
        if self._mock:
            self.log.warning("Auth mocking enabled.")
        self.auth_header_name = kwargs.pop('auth_header_name',
                                           'X-Portal-Authorization')
        self.username_claim_field = kwargs.pop('username_claim_field', 'uid')

    @log_call
    def process_request(self, req, resp):
        '''Get auth token from request.  Raise if it does not validate.'''
        if self._mock:
            # Pretend we had a token and create mock user
            self.user = make_mock_user()
            self.log.debug("Mocked out process_request")
            return
        auth_hdr = req.get_header(self.auth_header_name)
        challenges = ['bearer "JWT"']
        # Clear user until authentication succeeds
        self.user = None
        if auth_hdr is None:
            errstr = ("Auth token required as header " +
                      "'{}'".format(self.auth_header_name))
            raise falcon.HTTPUnauthorized('Auth token required',
                                          errstr,
                                          challenges)
        if auth_hdr.split()[0].lower() != 'bearer':
            raise falcon.HTTPUnauthorized('Incorrect token format',
                                          'Auth header must be "bearer".',
                                          challenges)
        token = auth_hdr.split()[1]
        try:
            claims = parse_access_token(token=token)
        except (RuntimeError, KeyError) as exc:
            raise falcon.HTTPForbidden(
                'Failed to verify JWT claims: {}'.format(exc))
        # Update user
        #  Yes, it's wasteful to do this each time, but since the user
        #  has no ORM backing it, it's a little bit of computation and some
        #  memory.  I don't think it will ever be an issue.
        self.user = self._make_user_from_claims(claims)
        self.parent.lsst_mgr.user = self.user
        self.parent.lsst_mgr.namespace_mgr.set_namespace(
            self.get_user_namespace())
        self.token = token

    @log_call
    def get_user_namespace(self):
        def_ns = get_default_namespace()
        if def_ns == "default":
            self.log.warning("Using 'default' namespace!")
            return "default"
        else:
            return "{}-{}".format(def_ns, self.user.escaped_name)

    def _make_user_from_claims(self, claims):
        with start_action(action_type="_make_user_from_claims"):
            username = claims[self.username_claim_field].lower()
            if '@' in username:
                # Process as if email and use localpart equivalent
                username = username.split('@')[0]
            escaped_name = quote(username, safe='@~')
            user = User()
            user.name = username
            user.escaped_name = escaped_name
            groupmap = {}
            auth_state = {}
            for grp in claims['isMemberOf']:
                name = grp['name']
                gid = grp.get('id')
                if not gid:
                    continue
                groupmap[name] = str(gid)
            uid = claims['uidNumber']
            auth_state['username'] = escaped_name
            auth_state['uid'] = uid
            auth_state['group_map'] = groupmap
            auth_state['claims'] = claims
            groups = list(groupmap.keys())
            user.groups = groups
            user.auth_state = auth_state
            # Update linked objects.
            am = self.parent.lsst_mgr.auth_mgr
            am.auth_state = auth_state
            am.group_map = auth_state['group_map']
            return user
