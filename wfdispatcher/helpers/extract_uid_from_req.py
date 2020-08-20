from eliot import log_call
from .extract_user_from_req import extract_user_from_req


@log_call
def extract_uid_from_req(req, hdr_name, claim_field):
    return extract_user_from_req(req, hdr_name, claim_field)["uid"]
