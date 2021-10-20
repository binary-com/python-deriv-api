from deriv_api.errors import *

def test_app_error_class():
    error = APIError("A error")
    assert isinstance(error, Exception)
    assert f'{error}' == 'APIError:A error'

def test_construction_error_class():
    error = ConstructionError("A error")
    assert isinstance(error, Exception)
    assert f'{error}' == 'ConstructionError:A error'