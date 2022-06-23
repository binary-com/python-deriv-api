import pytest
import re
from deriv_api.middlewares import MiddleWares

def test_middlewares():
    middlewares = MiddleWares()
    isinstance(middlewares, MiddleWares)

    with pytest.raises(Exception, match = r"should be a string") as err:
       MiddleWares({123: lambda i: i+1})

    with pytest.raises(Exception, match = r"should be a Callable") as err:
       MiddleWares({"name": 123})

    with pytest.raises(Exception, match = r"not supported"):
        MiddleWares({"hello": lambda i: i})

    call_args = []
    def send_will_be_called(*args):
        nonlocal call_args
        call_args = args
    middlewares.add('sendWillBeCalled', send_will_be_called)
    middlewares.call('sendWillBeCalled', 123)
    assert call_args == (123,)