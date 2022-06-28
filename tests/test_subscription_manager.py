import pytest

from deriv_api.subscription_manager import SubscriptionManager, get_msg_type
from reactivex.subject import Subject
from reactivex import Observable
import asyncio
from deriv_api.errors import APIError

mocked_response = {}


class API:
    def __init__(self):
        self.mocked_response = {}
        self.send_and_get_source_request = {}
        self.send_request = {}
        self.send_and_get_source_called = 0
        self.send_called = 0

    def send_and_get_source(self, request: dict) -> Subject:
        self.subject = Subject()
        self.send_and_get_source_called = self.send_and_get_source_called + 1
        self.send_and_get_source_request[self.send_and_get_source_called] = request
        return self.subject

    async def send(self, request: dict):
        self.send_called = self.send_called + 1
        self.send_request[self.send_called] = request
        return request

    async def emit(self):
        await asyncio.sleep(0.1)
        self.subject.on_next(self.mocked_response)

    def sanity_errors(self):
        class SanityErrors:
            def next(self, error):
                return error
        return SanityErrors()
    def add_task(self, task, name):
        asyncio.create_task(task, name=f"mocked_api:{name}")

def test_get_msg_type():
    assert get_msg_type({'hello': 1}) is None
    assert get_msg_type({'proposal': 1}) == 'proposal'


@pytest.mark.asyncio
async def test_subscribe():
    api: API = API()
    subscription_manager = SubscriptionManager(api)
    subs_id = 'ID11111'
    api.mocked_response = {"msg_type": "proposal", 'subscription': {'id': subs_id}}
    assert not subscription_manager.source_exists({'proposal': 1}), "at start there is no such source"
    with pytest.raises(APIError, match='Subscription type is not found in deriv-api'):
        await subscription_manager.subscribe({"no such type"})
    # get source first time
    source, emit = await asyncio.gather(subscription_manager.subscribe({'proposal': 1}), api.emit())
    assert isinstance(source, Observable)
    assert api.send_and_get_source_called == 1
    assert api.send_and_get_source_request[1] == {'proposal': 1, 'subscribe': 1}
    assert api.send_request == {}
    # get source second time
    api.__init__()
    source2, emit = await asyncio.gather(subscription_manager.subscribe({'proposal': 1}), api.emit())
    assert api.send_and_get_source_called == 0
    assert (source is source2), "same result"
    assert (source is subscription_manager.get_source({'proposal': 1})), 'source is in the cache'
    assert subscription_manager.source_exists({'proposal': 1}), "source in the cache"
    forget_result = await subscription_manager.forget(subs_id)
    assert api.send_called == 1
    assert forget_result == {'forget': subs_id}
    assert api.subject.is_disposed, "source is disposed"

    # test buy subscription
    api.__init__()
    subs_id = 'ID22222'
    api.mocked_response = {
        "buy": {
            "contract_id": 12345
        },
        "msg_type": "buy",
        "subscription": {
            "id": subs_id
        }
    }

    request = {
        "buy": 1,
        "price": 100,
    }
    source, emit = await asyncio.gather(subscription_manager.subscribe(request), api.emit())
    assert api.send_and_get_source_called == 1 , "send_and_get_source called once"
    assert isinstance(source, Observable)
    request = {
        'proposal_open_contract': 1,
        'contract_id': 12345
    }
    api.__init__()
    source2, emit = await asyncio.gather(subscription_manager.subscribe(request), api.emit())
    assert api.send_and_get_source_called == 0 , "send_and_get_source not called"
    assert source is source2, '"buy" source and "proposal_open_contract" source are same one and cached'
    await subscription_manager.forget(subs_id)
    api.__init__()
    source2, emit = await asyncio.gather(subscription_manager.subscribe(request), api.emit())
    assert api.send_and_get_source_called == 1 , "cache is cleared so the new call will get"
    assert source2 is not source, "new source is not the old one"

@pytest.mark.asyncio
async def test_forget_all():
    api = API()
    subscription_manager = SubscriptionManager(api)
    result = await subscription_manager.forget_all("hello")
    assert result == {'forget_all': ["hello"]}
