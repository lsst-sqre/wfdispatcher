from eliot import start_action
from jupyterhubutils import LoggableChild
from ..helpers.make_mock_user import make_mock_user
from ..helpers.extract_user_from_req import extract_user_from_req


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
        self.users = {}

    def process_request(self, req, resp):
        '''Get auth token from request.  Raise if it does not validate.'''
        with start_action(action_type="process_request/extract_auth"):
            if self._mock:
                # Pretend we had a token and create mock user
                self.user = make_mock_user()
                self.log.debug("Mocked out process_request")
                return
            user = extract_user_from_req(req, self.auth_header_name,
                                         self.username_claim_field)
            uid = user.uid
            self.users[uid] = user
