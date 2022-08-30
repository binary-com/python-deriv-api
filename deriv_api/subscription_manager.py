from deriv_api.utils import dict_to_cache_key
from deriv_api.errors import APIError
from deriv_api.streams_list import streams_list
from reactivex import operators as op
from reactivex.subject import Subject
from reactivex import Observable
from typing import Optional, Union
__pdoc__ = {
    'deriv_api.subscription_manager.SubscriptionManager.complete_subs_by_ids': False,
    'deriv_api.subscription_manager.SubscriptionManager.complete_subs_by_key': False,
    'deriv_api.subscription_manager.SubscriptionManager.create_new_source': False,
    'deriv_api.subscription_manager.SubscriptionManager.get_source': False,
    'deriv_api.subscription_manager.SubscriptionManager.remove_key_on_error': False,
    'deriv_api.subscription_manager.SubscriptionManager.save_subs_id': False,
    'deriv_api.subscription_manager.SubscriptionManager.save_subs_per_msg_type': False,
    'deriv_api.subscription_manager.SubscriptionManager.source_exists': False,
    'deriv_api.subscription_manager.SubscriptionManager.forget': False,
    'deriv_api.subscription_manager.SubscriptionManager.forget_all': False,
    'deriv_api.subscription_manager.get_msg_type': False
}


class SubscriptionManager:
    """
        Subscription Manager - manage subscription channels

        Makes sure there is always only one subscription channel for all requests of subscriptions,
        keeps a history of received values for the subscription of ticks and forgets channels that
        do not have subscribers. It also ensures that subscriptions are revived after connection
        drop/account changed.

        Parameters
        ----------
            api : deriv_api.DerivAPI

        Example
        -------
        - create a new subscription for R_100
        >>> source_tick_50: Observable  = await api.subscribe({'ticks': 'R_50'})
        >>> subscription_id = 0
        >>> def tick_50_callback(data):
        >>>     global subscription_id
        >>>     subscription_id = data['subscription']['id']
        >>>     print(data)
        >>> source_tick_50.subscribe(tick_50_callback)

        - forget all ticks
        >>> await api.forget_all('ticks')

        - forget based on subscription id
        >>> await api.forget(subscription_id)
        """

    def __init__(self, api):
        self.api = api
        self.sources: dict = {}
        self.orig_sources: dict = {}
        self.subs_id_to_key: dict = {}
        self.key_to_subs_id: dict = {}
        self.buy_key_to_contract_id: dict = {}
        self.subs_per_msg_type: dict = {}

    async def subscribe(self, request: dict) -> Observable:
        """
        Subscribe to a given request, returns a stream of new responses,
        Errors should be handled by the user of the stream

        Example
        -------
        >>> ticks = api.subscribe({ 'ticks': 'R_100' })
        >>> ticks.subscribe(call_back_function)

        Parameters
        ----------
        request : dict
            A request object acceptable by the API

        Returns
        -------
            Observable
                An RxPY SObservable
        """
        if not get_msg_type(request):
            raise APIError('Subscription type is not found in deriv-api')

        if self.source_exists(request):
            return self.get_source(request)

        new_request: dict = request.copy()
        new_request['subscribe'] = 1
        return await self.create_new_source(new_request)

    def get_source(self, request: dict) -> Optional[Subject]:
        """
        To get the source from the source list stored in sources

        Parameters
        ----------
        request : dict
            Request object

        Returns
        -------
            Returns source observable if exists, otherwise returns None
        """
        key: bytes = dict_to_cache_key(request)
        if key in self.sources:
            return self.sources[key]

        # if we have a buy subscription reuse that for poc
        for c in self.buy_key_to_contract_id.values():
            if c['contract_id'] == request['contract_id']:
                return self.sources[c['buy_key']]

        return None

    def source_exists(self, request: dict):
        """
        Get the source by request

        Parameters
        ----------
        request : dict
            A request object

        Returns
        -------
            Returns source observable if exists in source list, otherwise None

        """
        return self.get_source(request)

    async def create_new_source(self, request: dict) -> Observable:
        """
        Create new source observable, stores it in source list and returns

        Parameters
        ----------
        request : dict
            A request object

        Returns
        -------
            Returns source observable
        """
        key: bytes = dict_to_cache_key(request)

        def forget_old_source() -> None:
            if key not in self.key_to_subs_id:
                return
            # noinspection PyBroadException
            try:
                self.api.add_task(self.forget(self.key_to_subs_id[key]), 'forget old subscription')
            except Exception as err:
                self.api.sanity_errors.on_next(err)
            return

        self.orig_sources[key]: Observable = self.api.send_and_get_source(request)
        source: Observable = self.orig_sources[key].pipe(
            op.finally_action(forget_old_source),
            op.share()
        )
        self.sources[key] = source
        self.save_subs_per_msg_type(request, key)

        async def process_response() -> None:
            # noinspection PyBroadException
            try:
                response = await source.pipe(op.first(), op.to_future())
                if request.get('buy'):
                    self.buy_key_to_contract_id[key] = {
                        'contract_id': response['buy']['contract_id'],
                        'buy_key': key
                    }
                self.save_subs_id(key, response['subscription'])
            except Exception:
                self.remove_key_on_error(key)

        self.api.add_task(process_response(), 'subs manager: process_response')
        return source

    async def forget(self, subs_id: str) -> dict:
        """
        Delete the source from source list, clears the subscription detail from subs_id_to_key and key_to_subs_id and
        make api call to unsubscribe the subscription
        Parameters
        ----------
        subs_id : str
            Subscription id

        Returns
        -------
            Returns dict - api response for forget call
        """
        self.complete_subs_by_ids(subs_id)
        return await self.api.send({'forget': subs_id})

    async def forget_all(self, *types) -> dict:
        """
        Unsubscribe all subscription's of given type. For each subscription, it deletes the source from source list,
        clears the subscription detail from subs_id_to_key and key_to_subs_id. Make api call to unsubscribe all the
        subscriptions of given types.
        Parameters
        ----------
        types : Positional argument
            subscription stream types example : ticks, candles

        Returns
        -------
            Response from API call
        """
        # To include subscriptions that were automatically unsubscribed
        # for example a proposal subscription is auto-unsubscribed after buy

        for t in types:
            for k in (self.subs_per_msg_type.get(t) or []):
                self.complete_subs_by_key(k)
            self.subs_per_msg_type[t] = []
        return await self.api.send({'forget_all': list(types)})

    def complete_subs_by_ids(self, *subs_ids):
        """
        Completes the subscription for the given subscription id's - delete the source from source list, clears the
        subscription detail from subs_id_to_key and key_to_subs_id. Mark the original source as complete.

        Parameters
        ----------
        subs_ids : Positional argument
            subscription ids

        """
        for subs_id in subs_ids:
            if subs_id in self.subs_id_to_key:
                key = self.subs_id_to_key[subs_id]
                self.complete_subs_by_key(key)

    def save_subs_id(self, key: bytes, subscription: Union[dict, None]):
        """
        Saves the subscription detail in subs_id_to_key and key_to_subs_id

        Parameters
        ----------
        key : bytes
            API call request key. Key for key_to_subs_id
        subscription : dict or None
            subscription details - subscription id

        """
        if not subscription:
            return self.complete_subs_by_key(key)

        subs_id = subscription['id']
        if subs_id not in self.subs_id_to_key:
            self.subs_id_to_key[subs_id] = key
            self.key_to_subs_id[key] = subs_id

        return None

    def save_subs_per_msg_type(self, request: dict, key: bytes):
        """
        Save the request's key in subscription per message type

        Parameters
        ----------
        request : dict
            API request object
        key : bytes
            API request key

        """
        msg_type = get_msg_type(request)
        if msg_type:
            self.subs_per_msg_type[msg_type] = self.subs_per_msg_type.get(msg_type) or []
            self.subs_per_msg_type[msg_type].append(key)
        else:
            self.api.sanity_errors.next(APIError('Subscription type is not found in deriv-api'))

    def remove_key_on_error(self, key: bytes):
        """
        Remove ths source from source list,  clears the subscription detail from subs_id_to_key and key_to_subs_id.
        Mark the original source as complete.

        Parameters
        ----------
        key : bytes
            Request object key in bytes. Used to identify the subscription stored in key_to_subs_id

        """
        return lambda: self.complete_subs_by_key(key)

    def complete_subs_by_key(self, key: bytes):
        """
        Identify the source from source list based on request object key and removes it. Clears the subscription detail
        from subs_id_to_key and key_to_subs_id. Mark the original source as complete.

        Parameters
        ----------
        key : bytes
            Request object key to identify the subscription stored in key_to_subs_id

        """
        if not key or not self.sources[key]:
            return

        # Delete the source
        del self.sources[key]
        orig_source: Subject = self.orig_sources.pop(key)

        try:
            # Delete the subs id if exist
            if key in self.key_to_subs_id:
                subs_id = self.key_to_subs_id[key]
                del self.subs_id_to_key[subs_id]
                # Delete the key
                del self.key_to_subs_id[key]

            # Delete the buy key to contract_id mapping
            del self.buy_key_to_contract_id[key]
        except KeyError:
            pass

        # Mark the source complete
        orig_source.on_completed()
        orig_source.dispose()


def get_msg_type(request: dict) -> str:
    """
    Get message type by request

    Parameters
    ----------
    request : dict
        Request

    Returns
    -------
        Returns the next item from the iterator
    """
    return next((x for x in streams_list if x in request), None)
