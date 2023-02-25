import asyncio
import json
import logging
import re
from asyncio import Future
from typing import Dict, Optional, Union, Coroutine

import websockets
from reactivex import operators as op
from reactivex.subject import Subject
from reactivex import Observable
from websockets.legacy.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosedOK, ConnectionClosed
from websockets.frames import Close

from deriv_api.cache import Cache
from deriv_api.easy_future import EasyFuture
from deriv_api.deriv_api_calls import DerivAPICalls
from deriv_api.errors import APIError, ConstructionError, ResponseError, AddedTaskError
from deriv_api.in_memory import InMemory
from deriv_api.subscription_manager import SubscriptionManager
from deriv_api.utils import is_valid_url
from deriv_api.middlewares import MiddleWares

# TODO NEXT subscribe is not calling deriv_api_calls. that's , args not verified. can we improve it ?

logging.basicConfig(
    format="%(asctime)s %(message)s",
    level=logging.ERROR
)

__pdoc__ = {
    'deriv_api.deriv_api.DerivAPI.send_and_get_source': False,
    'deriv_api.deriv_api.DerivAPI.api_connect': False,
    'deriv_api.deriv_api.DerivAPI.get_url': False,
    'deriv_api.deriv_api.DerivAPI.add_task': False,
    'deriv_api.deriv_api.DerivAPI.delete_from_expect_response': False,
    'deriv_api.deriv_api.DerivAPI.disconnect': False,
    'deriv_api.deriv_api.DerivAPI.send': False,
    'deriv_api.deriv_api.DerivAPI.wsconnection': False,
    'deriv_api.deriv_api.DerivAPI.storage': False,
}


class DerivAPI(DerivAPICalls):
    """
    The minimum functionality provided by DerivAPI, provides direct calls to the API.
    `api.cache` is available if you want to use the cached data

    Examples
    --------
    - Pass the arguments needed to create a connection:
    >>> api = DerivAPI(endpoint='ws://...', app_id=1234)

    - create and use a previously opened connection:
    >>> connection = await websockets.connect('ws://...')
    >>> api = DerivAPI(connection=connection)

    Parameters
    ----------
        options : dict with following keys
            connection : websockets.WebSocketClientProtocol
                A ready to use connection
            endpoint : String
                API server to connect to
            app_id : String
                Application ID of the API user
            lang : String
                Language of the API communication
            brand : String
                Brand name
            middleware : MiddleWares
                middlewares to call on certain API actions. Now two middlewares are supported: sendWillBeCalled and
                sendIsCalled
    Properties
    ----------
    cache: Cache
        Temporary cache default to InMemory
    storage : Cache
        If specified, uses a more persistent cache (local storage, etc.)
    events: Observable
        An Observable object that will send data when events like 'connect', 'send', 'message' happen
    """

    storage: None

    def __init__(self, **options: str) -> None:
        endpoint = options.get('endpoint', 'frontend.binaryws.com')
        lang = options.get('lang', 'EN')
        brand = options.get('brand', '')
        cache = options.get('cache', InMemory())
        storage: any = options.get('storage')
        self.middlewares: MiddleWares = options.get('middlewares', MiddleWares())
        self.wsconnection: Optional[WebSocketClientProtocol] = None
        self.wsconnection_from_inside = True
        self.shouldReconnect = False
        self.events: Subject = Subject()
        if options.get('connection'):
            self.wsconnection: Optional[WebSocketClientProtocol] = options.get('connection')
            self.wsconnection_from_inside = False
        else:
            if not options.get('app_id'):
                raise ConstructionError('An app_id is required to connect to the API')

            connection_argument = {
                'app_id': str(options.get('app_id')),
                'endpoint_url': self.get_url(endpoint),
                'lang': lang,
                'brand': brand
            }
            self.__set_api_url(connection_argument)
            self.shouldReconnect = True

        self.storage: Optional[Cache] = None
        if storage:
            self.storage = Cache(self, storage)
        # If we have the storage look that one up
        self.cache = Cache(self.storage if self.storage else self, cache)

        self.req_id = 0
        self.pending_requests: Dict[str, Subject] = {}
        # resolved: connected  rejected: disconnected  pending: not connected yet
        self.connected = EasyFuture()
        self.subscription_manager: SubscriptionManager = SubscriptionManager(self)
        self.sanity_errors: Subject = Subject()
        self.expect_response_types = {}
        self.wait_data_task = EasyFuture().set_result(1)
        self.add_task(self.api_connect(), 'api_connect')
        self.add_task(self.__wait_data(), 'wait_data')

    async def __wait_data(self):
        await self.connected
        while self.connected.is_resolved():
            try:
                data = await self.wsconnection.recv()
            except ConnectionClosed as err:
                if self.connected.is_resolved():
                    self.connected = EasyFuture().reject(err)
                    self.connected.exception()  # call it to hide the warning of 'exception never retrieved'
                self.sanity_errors.on_next(err)
                break
            except Exception as err:
                self.sanity_errors.on_next(err)
                continue
            response = json.loads(data)

            self.events.on_next({'name': 'message', 'data': response})
            # TODO NEXT onopen onclose, can be set by await connection
            req_id = response.get('req_id', None)
            if not req_id or req_id not in self.pending_requests:
                self.sanity_errors.on_next(APIError("Extra response"))
                continue
            expect_response: Future = self.expect_response_types.get(response['msg_type'])
            if expect_response and not expect_response.done():
                expect_response.set_result(response)
            request = response['echo_req']

            # When one of the child subscriptions of `proposal_open_contract` has an error in the response,
            # it should be handled in the callback of consumer instead. Calling `error()` with parent subscription
            # will mark the parent subscription as complete and all child subscriptions will be forgotten.

            is_parent_subscription = request and request.get('proposal_open_contract') and not request.get(
                'contract_id')
            if response.get('error') and not is_parent_subscription:
                self.pending_requests[req_id].on_error(ResponseError(response))
                continue

            # on_error will stop a subject object
            if self.pending_requests[req_id].is_stopped and response.get('subscription'):
                # Source is already marked as completed. In this case we should
                # send a forget request with the subscription id and ignore the response received.
                subs_id = response['subscription']['id']
                self.add_task(self.forget(subs_id), 'forget subscription')
                continue

            self.pending_requests[req_id].on_next(response)

    def __set_api_url(self, connection_argument: dict) -> None:
        """
        Construct the websocket request url

        Parameters
        ----------
        connection_argument : dict

        """
        self.api_url = connection_argument.get('endpoint_url') + "/websockets/v3?app_id=" + connection_argument.get(
            'app_id') + "&l=" + connection_argument.get('lang') + "&brand=" + connection_argument.get('brand')

    def __get_api_url(self) -> str:
        """
            Returns the api request url

        Returns
        -------
            websocket api request url
        """
        return self.api_url

    def get_url(self, original_endpoint: str) -> Union[str, ConstructionError]:
        """
        Validate and return the url

        Parameters
        ----------
        original_endpoint : str
            endpoint argument passed to constructor

        Returns
        -------
            Returns api url. If validation fails then throws constructionError

        """
        if not isinstance(original_endpoint, str):
            raise ConstructionError(f"Endpoint must be a string, passed: {type(original_endpoint)}")

        match = re.match(r'((?:\w*://)*)(.*)', original_endpoint).groups()
        protocol = match[0] if match[0] == "ws://" else "wss://"
        endpoint = match[1]

        url = protocol + endpoint
        if not is_valid_url(url):
            raise ConstructionError(f'Invalid URL:{original_endpoint}')

        return url

    async def api_connect(self) -> websockets.WebSocketClientProtocol:
        """
            Make a websockets connection and returns WebSocketClientProtocol
        Returns
        -------
            Returns websockets.WebSocketClientProtocol
        """
        if not self.wsconnection and self.shouldReconnect:
            self.events.on_next({'name': 'connect'})
            self.wsconnection = await websockets.connect(self.api_url)
        if self.connected.is_pending():
            self.connected.resolve(True)
        else:
            self.connected = EasyFuture().resolve(True)
        return self.wsconnection

    async def send(self, request: dict) -> dict:
        """
        Send the API call and returns response

        Parameters
        ----------
        request : dict
            API request

        Returns
        -------
            API response
        """

        send_will_be_called = self.middlewares.call('sendWillBeCalled', {'request': request})
        if send_will_be_called:
            return send_will_be_called

        self.events.on_next({'name': 'send', 'data': request})
        response_future = self.send_and_get_source(request).pipe(op.first(), op.to_future())

        response = await response_future
        self.cache.set(request, response)
        if self.storage:
            self.storage.set(request, response)
        send_is_called = self.middlewares.call('sendIsCalled', {'response': response, 'request': request})
        if send_is_called:
            return send_is_called
        return response


    def send_and_get_source(self, request: dict) -> Subject:
        """
        Send message and returns Subject

        Parameters
        ----------
        request : dict
            API request

        Returns
        -------
            Returns the Subject
        """
        pending = Subject()
        if 'req_id' not in request:
            self.req_id += 1
            request['req_id'] = self.req_id
        self.pending_requests[request['req_id']] = pending

        async def send_message():
            try:
                await self.connected
                await self.wsconnection.send(json.dumps(request))
            except Exception as err:
                pending.on_error(err)

        self.add_task(send_message(), 'send_message')
        return pending

    async def subscribe(self, request: dict) -> Observable:
        """
        Subscribe to a given request

        Parameters
        ----------
            request : dict
                Subscribe request

        Example
        -------
        >>> proposal_subscription = api.subscribe({"proposal_open_contract": 1, "contract_id": 11111111, "subscribe": 1})

        Returns
        -------
            Observable
        """

        return await self.subscription_manager.subscribe(request)

    async def forget(self, subs_id: str) -> dict:
        """
        Forget / unsubscribe the specific subscription.

        Parameters
        ----------
            subs_id : str
                subscription id

        Returns
        -------
            Returns dict
        """

        return await self.subscription_manager.forget(subs_id)

    async def forget_all(self, *types) -> dict:
        """
        Forget / unsubscribe the subscriptions of given types.

        Possible values are: 'ticks', 'candles', 'proposal', 'proposal_open_contract', 'balance', 'transaction'

        Parameter
        ---------
            *types : Any number of non-keyword arguments
        Example
        -------
            api.forget_all("ticks", "candles")

        Returns
        -------
            Returns the dict
        """

        return await self.subscription_manager.forget_all(*types)

    async def disconnect(self) -> None:
        """
        Disconnect the websockets connection

        """
        if not self.connected.is_resolved():
            return
        self.connected = EasyFuture().reject(ConnectionClosedOK(None, Close(1000, 'Closed by disconnect')))
        self.connected.exception()  # fetch exception to avoid the warning of 'exception never retrieved'
        if self.wsconnection_from_inside:
            # TODO NEXT reconnect feature
            self.shouldReconnect = False
            self.events.on_next({'name': 'close'})
            await self.wsconnection.close()

    def expect_response(self, *msg_types):
        """
        Expect specific message types

        Parameters
        ----------
            *msg_types : variable number of non-key string argument
                Expect these types to be received by the API
        Returns
        -------
             Resolves to a single response or an array        
        """
        for msg_type in msg_types:
            if msg_type not in self.expect_response_types:
                future: Future = asyncio.get_event_loop().create_future()

                async def get_by_msg_type(a_msg_type):
                    nonlocal future
                    val = await self.cache.get_by_msg_type(a_msg_type)
                    if not val and self.storage:
                        val = self.storage.get_by_msg_type(a_msg_type)
                    if val:
                        future.set_result(val)

                self.add_task(get_by_msg_type(msg_type), 'get_by_msg_type')
                self.expect_response_types[msg_type] = future

        # expect on a single response returns a single response, not a list
        if len(msg_types) == 1:
            return self.expect_response_types[msg_types[0]]

        return asyncio.gather(map(lambda t: self.expect_response_types[t], msg_types))

    def delete_from_expect_response(self, request: dict):
        """
        Delete the given request message type from expect_response_types

        Parameters
        ----------
        request : dict

        """
        response_type = None
        for k in self.expect_response_types.keys():
            if k in request:
                response_type = k
                break

        if response_type and self.expect_response_types[response_type] \
                and self.expect_response_types[response_type].done():
            del self.expect_response_types[response_type]

    def add_task(self, coroutine: Coroutine, name: str) -> None:
        """
        Add coroutine object to execution

        Parameters
        ----------
        coroutine : Coroutine
            Coroutine object
        name: str
            name of the Coroutine

        """
        name = 'deriv_api:' + name

        async def wrap_coro(coru: Coroutine, pname: str) -> None:
            try:
                await coru
            except Exception as err:
                self.sanity_errors.on_next(AddedTaskError(err, pname))

        asyncio.create_task(wrap_coro(coroutine, name), name=name)

    async def clear(self):
        """
        Disconnect and cancel all the tasks        
        """
        await self.disconnect()
        for task in asyncio.all_tasks():
            if re.match(r"^deriv_api:", task.get_name()):
                task.cancel('deriv api ended')
