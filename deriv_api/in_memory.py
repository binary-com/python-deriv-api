
__pdoc__ = {
    'deriv_api.in_memory.InMemory.get': False,
    'deriv_api.in_memory.InMemory.get_by_msg_type': False,
    'deriv_api.in_memory.InMemory.has': False,
    'deriv_api.in_memory.InMemory.set': False
}


class InMemory:
    """An in memory storage which can be used for caching"""

    def __init__(self) -> None:
        self.store = {}
        self.type_store = {}

    def has(self, key: bytes) -> bool:
        """
        Check the key exists in the store and returns true if exists.

        Parameters
        ----------
        key : bytes
            Request object key

        Returns
        -------
            Returns true if the request key exists in memory
        """
        return key in self.store

    # we should serialize key (utils/dict_to_cache_key) before we store it
    # At first I want to use it directly here.
    # But from js version of deriv-api logic, user can choose cache object freely.
    # So we shouldn't suppose other cache module will serialize the key.
    # So we should always call serialize in the caller module
    def get(self, key: bytes) -> dict:
        """
        Get the response stored in for the given request by key

        Parameters
        ----------
        key : bytes
            Request of object key

        Returns
        -------
            Response object received and stored in for the given request key
        """
        return self.store[key]

    def get_by_msg_type(self, msg_type: str) -> dict:
        """
        Get the response stored in based on message type

        Parameters
        ----------
        msg_type : str
            Request object msg_type

        Returns
        -------
            Response object stored in for the given message type
        """
        return self.type_store.get(msg_type)

    def set(self, key: bytes, value: dict) -> None:
        """
        Stores the response of the given request

        Parameters
        ----------
        key : bytes
            Request object key
        value : dict
            Response object received from api
        """
        self.store[key] = value
        self.type_store[value['msg_type']] = value
