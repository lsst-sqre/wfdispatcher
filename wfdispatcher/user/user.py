import asyncio


class User(object):
    '''This looks, not coincidentally, like the JupyterHub User object.

    That means it has the following attributes:
      name (str)
      escaped_name (str)
      groups (list)
      auth_state (dict)
      get_auth_state (coroutine)
      set_auth_state (coroutine) is OMITTED

    However, unlike the JupyterHub User, there's no backing ORM.

    Set these attributes immediately after creating the User object and
    then leave them alone.
    '''

    def __init__(self, *args, **kwargs):
        self.name = None
        self.escaped_name = None
        self.groups = []
        self.auth_state = {}

    async def get_auth_state(self):
        return self.auth_state
