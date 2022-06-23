from typing import Callable, Union

_implemented_middlewares = ['sendWillBeCalled', 'sendIsCalled']


class MiddleWares:
    """A class that help to manage middlewares"""

    def __init__(self, middlewares: dict = {}):
        self.middlewares = {}
        for name in middlewares.keys():
            self.add(name, middlewares[name])

    def add(self, name: str, code: Callable[..., bool]) -> None:
        if not isinstance(name, str):
            raise Exception(f"name {name} should be a string")
        if not isinstance(code, Callable):
            raise Exception(f"code {code} should be a Callable object")
        if name in _implemented_middlewares:
            self.middlewares[name] = code
        else:
            raise Exception(f"{name} is not supported in middleware")

    def call(self, name: str, args: dict) -> Union[None, dict]:
        """
        Call middleware and return the result if there is such middleware

        Parameters
        ----------
        name: string
        args: list
            the args that will feed to middleware

        Returns
        -------
            If there is such middleware, then return the result of middleware
            else return None
        """

        if name not in self.middlewares:
            return None
        return self.middlewares[name](args)
