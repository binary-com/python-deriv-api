from deriv_api.in_memory import InMemory


def test_in_memory():
    obj = InMemory()
    assert isinstance(obj, InMemory)
    obj.set('hello', {'msg_type': 'test_type', 'val': 123})
    assert obj.has('hello')
    assert obj.get('hello')['val'] == 123
    assert obj.get_by_msg_type('test_type') == obj.get('hello')
    assert obj.has('no such key') is False
