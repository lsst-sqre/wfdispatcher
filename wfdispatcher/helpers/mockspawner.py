from jupyterhubutils import LoggableChild


class MockSpawner(LoggableChild):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_namespace_quotas = kwargs.pop('enable_namespace_quotas',
                                                  True)
