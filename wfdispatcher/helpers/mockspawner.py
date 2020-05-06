from jupyterhubutils import LoggableChild


class MockSpawner(LoggableChild):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_namespace_quotas = kwargs.pop('enable_namespace_quotas',
                                                  True)
        user = kwargs.pop('user', None)
        if not user:
            authenticator = parent.get('authenticator', None)
            if authenticator:
                user = authenticator.get('user')
        self.user = user
