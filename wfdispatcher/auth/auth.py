from eliot import start_action
from rubin_jupyter_utils.hub import LoggableChild
from ..helpers.extract_user_from_req import extract_user_from_req
from ..helpers.make_mock_user import make_mock_user
from ..helpers.mockspawner import MockSpawner


class AuthenticatorMiddleware(LoggableChild):
    def __init__(self, *args, **kwargs):
        self.parent = None
        self.token = None
        self.user = None
        super().__init__(*args, **kwargs)  # Sets self.parent
        self.log.debug("Creating Authenticator.")
        self._mock = kwargs.pop("_mock", False)
        if self._mock:
            self.log.warning("Auth mocking enabled.")
        self.auth_header_name = kwargs.pop(
            "auth_header_name", "X-Portal-Authorization"
        )
        self.username_claim_field = kwargs.pop("username_claim_field", "uid")
        self.user = None
        self.spawner = None

    def process_request(self, req, resp):
        """Get auth token from request.  Raise if it does not validate."""
        with start_action(action_type="process_request/extract_auth"):
            user = None
            if self._mock:
                # Pretend we had a token and create mock user
                user = make_mock_user()
                self.log.debug("Mocked out process_request")
            else:
                user = extract_user_from_req(
                    req, self.auth_header_name, self.username_claim_field
                )
            if not user:
                raise RuntimeError("Could not determine user!")
            self.set_auth_fields(user=user)

    def set_auth_fields(self, user=None):
        """Given a user, create appropriate attributes."""
        if not user:
            self.log.info("Setting auth fields from existing user.")
            user = self.user
        if not user:
            raise RuntimeError("Could not determine user!")
        self.spawner = MockSpawner(parent=self, user=user)
        self.user = user
