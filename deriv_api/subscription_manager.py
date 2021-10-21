import asyncio

from deriv_api.utils import dict_to_cache_key
from deriv_api.errors import APIError
from rx import operators as op
from rx.subject import Subject
from rx import Observable
from typing import Optional

# streams_list is the list of subscriptions msg_types available.
# Please add / remove based on current available streams in api.
# Refer https: // developers.binary.com /
# TODO NEXT auto generate this one
streams_list = ['balance', 'candles', 'p2p_advertiser', 'p2p_order', 'proposal',
                'proposal_array', 'proposal_open_contract', 'ticks', 'ticks_history', 'transaction',
                'website_status', 'buy']

__pdoc__ = {
    'deriv_api.subscription_manager.SubscriptionManager.complete_subs_by_ids' : False,
    'deriv_api.subscription_manager.SubscriptionManager.complete_subs_by_key' : False,
    'deriv_api.subscription_manager.SubscriptionManager.create_new_source': False,
    'deriv_api.subscription_manager.SubscriptionManager.get_source': False,
    'deriv_api.subscription_manager.SubscriptionManager.remove_key_on_error': False,
    'deriv_api.subscription_manager.SubscriptionManager.save_subs_id': False,
    'deriv_api.subscription_manager.SubscriptionManager.save_subs_per_msg_type': False,
    'deriv_api.subscription_manager.SubscriptionManager.create_new_sourcesource_exists': False,
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

    async def subscribe(self, request: dict) -> Subject:
        """
        Subscribe to a given request, returns a stream of new responses,
        Errors should be handled by the user of the stream

        Example
        -------
        >>> ticks = api.subscribe({ 'ticks': 'R_100' });
        >>> ticks.subscribe(call_back_function)

        Parameter
        ---------
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
        key: str = dict_to_cache_key(request)
        if key in self.sources:
            return self.sources[key]

        # if we have a buy subscription reuse that for poc
        for c in self.buy_key_to_contract_id.values():
            if c['contract_id'] == request['contract_id']:
                return self.sources[c['buy_key']]

        return None

    def source_exists(self, request: dict):
        return self.get_source(request)

    async def create_new_source(self, request: dict) -> Subject:
        key: str = dict_to_cache_key(request)
        def forget_old_source():
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
        async def process_response():
            # noinspection PyBroadException
            try:
                response = await source.pipe(op.first(), op.to_future())
                if request.get('buy'):
                    self.buy_key_to_contract_id[key] = {
                        'contract_id': response['buy']['contract_id'],
                        'buy_key': key
                    }
                self.save_subs_id(key, response['subscription'])
            except Exception as err:
                self.remove_key_on_error(key)

        self.api.add_task(process_response(), 'subs manager: process_response')
        return source

    async def forget(self, subs_id):
        self.complete_subs_by_ids(subs_id)
        return await self.api.send({'forget': subs_id})

    async def forget_all(self, *types):
        # To include subscriptions that were automatically unsubscribed
        # for example a proposal subscription is auto-unsubscribed after buy

        for t in types:
            for k in (self.subs_per_msg_type.get(t) or []):
                self.complete_subs_by_key(k)
            self.subs_per_msg_type[t] = []
        return await self.api.send({'forget_all': list(types)})

    def complete_subs_by_ids(self, *subs_ids):
        for subs_id in subs_ids:
            if subs_id in self.subs_id_to_key:
                key = self.subs_id_to_key[subs_id]
                self.complete_subs_by_key(key)

    def save_subs_id(self, key, subscription):
        if not subscription:
            return self.complete_subs_by_key(key)

        subs_id = subscription['id']
        if subs_id not in self.subs_id_to_key:
            self.subs_id_to_key[subs_id] = key
            self.key_to_subs_id[key] = subs_id

        return None

    def save_subs_per_msg_type(self, request, key):
        msg_type = get_msg_type(request)
        if msg_type:
            self.subs_per_msg_type[msg_type] = self.subs_per_msg_type.get(msg_type) or []
            self.subs_per_msg_type[msg_type].append(key)
        else:
            self.api.sanity_errors.next(APIError('Subscription type is not found in deriv-api'))

    def remove_key_on_error(self, key):
        return lambda: self.complete_subs_by_key(key)

    def complete_subs_by_key(self, key):
        if not key or not self.sources[key]:
            return

        # Delete the source
        del self.sources[key]
        orig_source: Subject = self.orig_sources.pop(key)

        try:
            # Delete the subs id if exist
            if(key in self.key_to_subs_id):
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


def get_msg_type(request) -> str:
    return next((x for x in streams_list if x in request), None)
