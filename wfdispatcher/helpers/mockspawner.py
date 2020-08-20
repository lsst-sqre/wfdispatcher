from rubin_jupyter_utils.hub import LoggableChild


class MockSpawner(LoggableChild):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_namespace_quotas = kwargs.pop(
            "enable_namespace_quotas", True
        )
        self.user = kwargs.pop("user", None)
        self.cached_auth_state = None
        if self.user:
            self.cached_auth_state = {
                "claims": self.user.claims,
                "access_token": self.user.access_token,
            }
