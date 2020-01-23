from jupyterhubutils import make_logger


class Loggable(object):
    log = None

    def __init__(self, *args, **kwargs):
        self.log = make_logger()
