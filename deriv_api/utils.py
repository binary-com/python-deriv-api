import pickle
import re

"""
Utility Methods
---------------
dict_to_cache_key(obj)
    convert the dictionary object to Pickled representation of object as bytes

is_valid_url(url)
    check the given url as a valid ws or wss url
"""


def dict_to_cache_key(obj: dict) -> bytes:
    """convert the dictionary object to Pickled representation of object as bytes

    param obj: request arguments
    return: Pickled representation of request object as bytes
    rtype: bytes
    """

    cloned_obj: dict = obj.copy()
    for key in ['req_id', 'passthrough', 'subscribe']:
        cloned_obj.pop(key, None)

    return pickle.dumps(cloned_obj)


def is_valid_url(url: str) -> bool:
    regex = re.compile(
        r'^(?:ws)s?://'  # ws:// or wss://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None
