import pytest
import re
from deriv_api.deriv_api_calls import DerivAPICalls, parse_args, validate_args

class DerivedDerivAPICalls(DerivAPICalls):
    async def send(self, args):
        return args

@pytest.mark.asyncio
async def test_deriv_api_calls(mocker):
    api = DerivedDerivAPICalls()
    assert isinstance(api, DerivAPICalls)
    assert (await api.account_closure({'account_closure': 1, 'reason': 'want'})) == {'account_closure': 1,
                                                                                    'reason': 'want'}, 'account_closure can get right result'
    with pytest.raises(ValueError, match='Required parameters missing: reason'):
        await api.account_closure({})


def test_parse_parse_args():
    assert parse_args(
        {'config': {'acc': {'type': 'boolean'}}, 'args': '1', 'method': 'acc', 'needs_method_arg': 1}) == {
               'acc': 1}, "method will be a key and arg will be value if arg is not a dict and needs_method_arg is true"
    assert parse_args(
        {'config': {'acc': {'type': 'boolean'}}, 'args': {'acc': '0'}, 'method': 'acc', 'needs_method_arg': 1}) == {
               'acc': 0}, "method value will from args if arg is a dict and needs_method_arg is true"
    assert parse_args({'config': {'acc': {'type': 'string'}}, 'args': {'hello': 0}, 'method': 'acc',
                                      'needs_method_arg': 1}) is None, "if arg is not in config, then return none"
    # test type
    assert parse_args(
        {'config': {'acc': {'type': 'string'}}, 'args': {'acc': 0}, 'method': 'acc', 'needs_method_arg': 1}) == {
               'acc': '0'}, "arg is string"
    assert parse_args(
        {'config': {'acc': {'type': 'numeric'}}, 'args': {'acc': '0'}, 'method': 'acc', 'needs_method_arg': 1}) == {
               'acc': 0}, "arg is numeric"
    assert parse_args(
        {'config': {'acc': {'type': 'boolean'}}, 'args': {'acc': '0'}, 'method': 'acc', 'needs_method_arg': 1}) == {
               'acc': 0}, "arg is boolean"

def test_validate_args():
    assert re.match('Requires an dict',validate_args({},""))
    assert validate_args({'k1': {'required': 1}, 'k2': {}}, {'k1': 1, 'k2': 2, 'k3': 3}) == '', 'required keys are there'
    error_msg = validate_args({'k1': {'required': 1}, 'k2': {'required': 1}}, {'k3': 1})
    assert re.search('k1', error_msg) and re.search('k2', error_msg), 'missed keys will be reported'
    config = {
        'k1': {'type': 'dict'},
        'k2': {'type': 'string'},
        'k3': {'type': 'numeric'},
        'k4': {'type': 'boolean'},
        'k5': {}
    }
    error_msg = validate_args(config, {'k1': 1, 'k2': 1, 'k3': 'aString', 'k4': 'aString'})
    assert re.search("dict value expected but found <class 'int'>: k1 ", error_msg)
    assert re.search("string value expected but found <class 'int'>: k2", error_msg)
    assert re.search("numeric value expected but found <class 'str'>: k3", error_msg)
    assert re.search("boolean value expected but found <class 'str'>: k4", error_msg)
    error_msg = validate_args(config, {'k1': {}, 'k2': "string", 'k3': 1, 'k4': True, 'k5': 1})
    assert error_msg == ''
