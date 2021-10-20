from deriv_api.cache import Cache
from deriv_api.errors import ConstructionError
from deriv_api.in_memory import InMemory
import pytest

class Api:
    def __init__(self):
        self.seq = 0
    async def send(self, request):
        # seq will change every time send is called
        self.seq = self.seq + 1
        return {'request': request, 'seq': self.seq, 'msg_type': request['msg_type']}

@pytest.mark.asyncio
async def test_cache():
    with pytest.raises(ConstructionError, match='Cache object needs an API to work'):
        Cache(None, None)
    api = Api();
    cache = Cache(api, InMemory())
    assert (await cache.send({'msg_type':"a message"})) == {'request': {'msg_type': 'a message'}, 'seq': 1, 'msg_type': 'a message'} , "api send is called first time"
    assert (await cache.send({'msg_type':"a message"})) == {'request': {'msg_type': 'a message'}, 'seq': 1, 'msg_type': 'a message'} , "date fetched from cache second time"
