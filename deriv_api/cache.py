from __future__ import annotations
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from deriv_api import DerivAPI
from deriv_api.deriv_api_calls import DerivAPICalls
from deriv_api.errors import ConstructionError
from deriv_api.utils import dict_to_cache_key
from deriv_api.in_memory import InMemory

__pdoc__ = {
    'deriv_api.cache.Cache.get': False,
    'deriv_api.cache.Cache.get_by_msg_type': False,
    'deriv_api.cache.Cache.has': False,
    'deriv_api.cache.Cache.send': False,
    'deriv_api.cache.Cache.set': False
}


class Cache(DerivAPICalls):
    """
        Cache - A class for implementing in-memory and persistent cache

        The real implementation of the underlying cache is delegated to the storage
        object (See the params).

        The storage object needs to implement the API.

        Examples
        --------
        - Read the latest active symbols
        >>> symbols = await api.active_symbols()

        - Read the data from cache if available
        >>> cached_symbols = await api.cache.active_symbols()

        Parameters
        ----------
            api : deriv_api.DerivAPI
                API instance to get data that is not cached
            storage : Object
                A storage instance to use for caching
        """

    def __init__(self, api: Union[DerivAPI, Cache], storage: Union[InMemory, Cache]) -> None:
        if not api:
            raise ConstructionError('Cache object needs an API to work')

        super().__init__()
        self.api = api
        self.storage = storage

    async def send(self, request: dict) -> dict:
        """Check if there is a cache for the request. If so then return that value.
        Otherwise send the request by the api

        Parameters
        ----------
        request : dict
            API request

        Returns
        -------
            API Response
        """
        if await self.has(request):
            return await self.get(request)

        response = await self.api.send(request)
        self.set(request, response)
        return response

    async def has(self, request: dict) -> bool:
        """Redirected to the method defined by the storage

        Parameters
        ----------
        request : dict
            API request

        Returns
        -------
            Returns true if the request exists
        """
        return self.storage.has(dict_to_cache_key(request))

    async def get(self, request: dict) -> dict:
        """Redirected to the method defined by the storage

        Parameters
        ----------
        request : dict
            API request

        Returns
        -------
            API response stored in
        """
        return self.storage.get(dict_to_cache_key(request))

    async def get_by_msg_type(self, msg_type: str) -> dict:
        """Redirected to the method defined by the storage

        Parameters
        ----------
        msg_type : str
            Request msg_type

        Returns
        -------
            Returns response stored in
        """
        return self.storage.get_by_msg_type(msg_type)

    def set(self, request: dict, response: dict) -> None:
        """Redirected to the method defined by the storage

        Parameters
        ----------
        request : dict
            API request
        response : dict
            API response
        """
        return self.storage.set(dict_to_cache_key(request), response)
