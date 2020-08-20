import falcon
from eliot import start_action


def extract_access_token_from_req(req, hdr_name):
    with start_action(action_type="extract_access_token_from_req"):
        auth_hdr = req.get_header(hdr_name)
        challenges = ['bearer "JWT"']
        # Clear user until authentication succeeds
        if auth_hdr is None:
            errstr = "Auth token required as header " + "'{}'".format(hdr_name)
            raise falcon.HTTPUnauthorized(
                "Auth token required", errstr, challenges
            )
        if auth_hdr.split()[0].lower() != "bearer":
            raise falcon.HTTPUnauthorized(
                "Incorrect token format",
                'Auth header must be "bearer".',
                challenges,
            )
        token = auth_hdr.split()[1]
        return token
