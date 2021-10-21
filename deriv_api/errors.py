def error_factory(class_type: str) -> object:
    class GenericError(Exception):
        def __init__(self, message: str):
            super().__init__(message)
            self.type = class_type
            self.message = message

        def __str__(self) -> str:
            return f'{self.type}:{self.message}'

    return GenericError


class APIError(error_factory('APIError')):
    pass


class ConstructionError(error_factory('ConstructionError')):
    pass


class ResponseError(Exception):
    def __init__(self, response: dict):
        super().__init__(response['error']['message'])
        self.request = response['echo_req']
        self.code = response['error']['code']
        self.message = response['error']['message']
        self.msg_type = response['msg_type']
        self.req_id = response.get('req_id')

    def __str__(self) -> str:
        return f"ResponseError: {self.message}"


class AddedTaskError(Exception):
    def __init__(self, exception, name):
        super().__init__()
        self.exception = exception
        self.name = name

    def __str__(self) -> str:
        return f"{self.name}: {str(self.exception)}"
