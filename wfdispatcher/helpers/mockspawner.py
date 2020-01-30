from jupyterhubutils import LoggableChild


class MockSpawner(LoggableChild):
    enable_namespace_quotas = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        enable_namespace_quotas = kwargs.pop('enable_namespace_quotas',
                                             self.enable_namespace_quotas)
        self.enable_namespace_quotas = enable_namespace_quotas
