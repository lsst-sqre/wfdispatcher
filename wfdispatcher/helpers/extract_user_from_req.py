import falcon
from eliot import start_action
from rubin_jupyter_utils.helpers import (
    get_execution_namespace,
    parse_access_token,
)
from urllib.parse import quote
from .extract_access_token_from_req import extract_access_token_from_req
from ..user.user import User


def extract_user_from_req(req, hdr_name, claim_fld):
    with start_action(action_type="extract_user_from_req"):
        token = extract_access_token_from_req(req, hdr_name)
        try:
            claims = parse_access_token(token=token)
        except (RuntimeError, KeyError) as exc:
            raise falcon.HTTPForbidden(
                "Failed to verify JWT claims: {}".format(exc)
            )
        username = claims[claim_fld]
        if not username:
            raise falcon.HTTPUnprocessableEntity(
                "Could not determine username from claim field {}!".format(
                    claim_fld
                )
            )
        username = username.lower()
        if "@" in username:
            # Process as if email and use localpart equivalent
            username = username.split("@")[0]
        e_ns = get_execution_namespace()
        if not e_ns:
            e_ns = "user"  # pick a reasonable default for user namespaces
        u_ns = "{}-{}".format(e_ns, quote(username))
        user = User(
            name=username,
            namespace=u_ns,
            uid=int(claims["uidNumber"]),
            access_token=token,
            claims=claims,
        )
        return user
