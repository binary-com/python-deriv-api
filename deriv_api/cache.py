from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deriv_api.deriv_api import DerivAPI
from typing import Union
from deriv_api.deriv_api_calls import DerivAPICalls
from deriv_api.errors import ConstructionError
from deriv_api.utils import dict_to_cache_key
from deriv_api.in_memory import InMemory


class Cache(DerivAPICalls):
    """
    Cache - A class for implementing in-memory and persistent cache

    The real implementation of the underlying cache is delegated to the storage
    object (See the params).

    The storage object needs to implement the API.

    example
    # Read the latest active symbols
    symbols = await api.activeSymbols();

    # Read the data from cache if available
    cached_symbols = await api.cache.activeSymbols();

    param {DerivAPI} api API instance to get data that is not cached
    param {Object} storage A storage instance to use for caching
    """

    def __init__(self, api: Union[DerivAPI, Cache], storage: Union[InMemory, Cache]) -> None:
        if not api:
            raise ConstructionError('Cache object needs an API to work')

        super().__init__()
        self.api = api
        self.storage = storage

    async def send(self, request: dict) -> dict:
        if await self.has(request):
            return await self.get(request)

        response = await self.api.send(request)
        self.set(request, response)
        return response

    async def has(self, request: dict) -> bool:
        """Redirected to the method defined by the storage"""
        return self.storage.has(dict_to_cache_key(request))

    async def get(self, request: dict) -> dict:
        """Redirected to the method defined by the storage"""
        return self.storage.get(dict_to_cache_key(request))

    async def get_by_msg_type(self, msg_type: str) -> dict:
        """Redirected to the method defined by the storage"""
        return self.storage.get_by_msg_type(msg_type)

    def set(self, request, response: dict) -> None:
        """Redirected to the method defined by the storage"""
        return self.storage.set(dict_to_cache_key(request), response)
