import falcon
from eliot import start_action


class RequireJSONMiddleware(object):
    def process_request(self, req, resp):
        with start_action(action_type="process_request/requireJSON"):
            if not req.client_accepts_json:
                raise falcon.HTTPNotAcceptable(
                    "This API only supports responses encoded as JSON.",
                    href="http://docs.examples.com/api/json",
                )

            if req.method in ("POST", "PUT"):
                if "application/json" not in req.content_type:
                    raise falcon.HTTPUnsupportedMediaType(
                        "This API only supports requests encoded as JSON.",
                        href="http://docs.examples.com/api/json",
                    )
