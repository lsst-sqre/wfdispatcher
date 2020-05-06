from jupyterhubutils import LoggableChild


class MockSpawner(LoggableChild):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_namespace_quotas = kwargs.pop('enable_namespace_quotas',
                                                  True)
        user = kwargs.pop('user', None)
        if not user:
            p0 = self.parent
            if p0 and hasattr(p0, 'authenticator'):
                authenticator = p0.authenticator
                if authenticator:
                    user = authenticator.user
        self.user = user
