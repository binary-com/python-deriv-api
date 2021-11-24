from deriv_api.utils import dict_to_cache_key
import pickle


def test_dict_to_cache_key():
    assert(pickle.loads(dict_to_cache_key({"hello": "world", "subscribe": 1, "passthrough": 1, "req_id": 1})) == {"hello": "world"})
