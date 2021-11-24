"""
.. include:: ../README.md
.. include:: ../docs/usage_examples.md
"""

__pdoc__ = {
    'deriv_api.errors': False,
    'deriv_api.utils': False,
    'deriv_api.easy_future': False
}

from .deriv_api import DerivAPI
from .errors import AddedTaskError, APIError, ConstructionError, ResponseError

