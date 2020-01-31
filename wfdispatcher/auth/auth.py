import datetime
import falcon
from jose import jwt
from jupyterhubutils import LoggableChild
from jupyterhubutils.utils import get_execution_namespace
from urllib.parse import quote
from ..helpers.make_mock_user import make_mock_user
from ..user.user import User


def get_default_namespace():
    ns = get_execution_namespace()
    if ns is None:
        ns = "default"
    return ns


class AuthenticatorMiddleware(LoggableChild):
    auth_header_name = 'X-Portal-Authorization'
    username_claim_field = 'uid'
    verify_signature = True
    verify_audience = True
    _secret = None
    parent = None
    user = None
    _mock = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log.debug("Creating Authenticator.")
        _mock = kwargs.pop('_mock', self._mock)
        self._mock = _mock
        if self._mock:
            self.log.warning("Auth mocking enabled.")
        else:
            verify_signature = kwargs.pop(
                'verify_signature', self.verify_signature)
            self.verify_signature = verify_signature
            if not verify_signature:
                self.log.warning("Not verifying signature.")
            verify_audience = kwargs.pop(
                'verify_audience', self.verify_audience)
            self.verify_audience = verify_audience
            if not verify_audience:
                self.log.warning("Not verifying audience.")
        auth_header_name = kwargs.pop(
            'auth_header_name', self.auth_header_name)
        self.auth_header_name = auth_header_name
        username_claim_field = kwargs.pop(
            'username_claim_field', self.username_claim_field)
        self.username_claim_field = username_claim_field

    def process_request(self, req, resp):
        '''Get auth token from request.  Raise if it does not validate.'''
        if self._mock:
            # Pretend we had a token and create mock user
            self.user = make_mock_user()
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
        claims = self.verify_jwt(token)
        if not claims:
            raise falcon.HTTPForbidden('Could not verify JWT')
        # Check expiration
        expiry = int(claims['exp'])
        now = int(datetime.datetime.utcnow().timestamp())
        if now > expiry:
            raise falcon.HTTPForbidden('JWT has expired')
        # Update user
        #  Yes, it's wasteful to do this each time, but since the user
        #  has no ORM backing it, it's a little bit of computation and some
        #  memory.  I don't think it will ever be an issue.
        self.user = self._make_user_from_claims(claims)
        self.parent.lsst_mgr.user = self.user
        self.parent.lsst_mgr.namespace_mgr.set_namespace(
            self.get_user_namespace())

    def get_user_namespace(self):
        def_ns = get_default_namespace()
        if def_ns == "default":
            self.log.warning("Using 'default' namespace!")
            return "default"
        else:
            return "{}-{}".format(def_ns, self.user.escaped_name)

    def verify_jwt(self, token):
        cfg = self.parent.lsst_mgr.config
        cert = cfg.jwt_signing_certificate
        aud = cfg.audience
        v_c = self.verify_signature
        v_a = self.verify_audience
        secret = None
        opts = {}
        if not v_a:
            opts["verify_aud"] = False
        # We do cache the signing certificate, to keep this routine
        #  from having to do I/O from disk (potentially, although in practice
        #  it'd end up in disk cache pretty quickly) on every access.
        if v_c:
            if not self._secret:
                with open(cert, 'r') as f:
                    secret = f.read()
                    self._secret = secret
        else:
            opts["verify_signature"] = False
        return jwt.decode(token, self._secret, audience=aud, options=opts)

    def _make_user_from_claims(self, claims):
        username = claims[self.username_claim_field]
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
