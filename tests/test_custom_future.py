import asyncio

import pytest
from deriv_api.easy_future import EasyFuture
from asyncio.exceptions import InvalidStateError, CancelledError
import sys

def test_custom_future():
    f1 = EasyFuture()
    assert f1.is_pending()
    f1.resolve("hello")
    assert f1.result() == "hello"
    assert f1.is_resolved()
    with pytest.raises(InvalidStateError, match="invalid state"):
        f1.reject("world")
    f2 = EasyFuture()
    f2.reject(Exception)
    assert f2.is_rejected()

@pytest.mark.asyncio
async def test_wrap():
    # test resolved
    f1 = asyncio.Future()
    f2 = EasyFuture.wrap(f1)
    assert isinstance(f2, EasyFuture)
    assert f1.get_loop() is f2.get_loop()
    assert f2.is_pending()
    f1.set_result("hello")
    await f2
    assert f2.result() == "hello"
    assert f2.done()

    # test reject
    f1 = asyncio.Future()
    f2 = EasyFuture.wrap(f1)
    f1.set_exception(Exception("hello"))
    with pytest.raises(Exception, match='hello'):
        await f2
    assert f2.done()
    assert f2.is_rejected()

    # test upstream cancel
    f1 = asyncio.Future()
    f2 = EasyFuture.wrap(f1)
    f1.cancel("hello")
    with pytest.raises(CancelledError, match='hello'):
        await f2
    assert f2.done()
    assert f2.is_cancelled()

    # test downstream cancel
    f1 = asyncio.Future()
    f2 = EasyFuture.wrap(f1)
    f2.cancel("hello")
    with pytest.raises(CancelledError, match='hello'):
        await f1
    assert f1.done()
    assert f1.cancelled()


@pytest.mark.asyncio
async def test_future_then():
    # test upstream ok
    # test callback future ok
    f1 = EasyFuture()
    def then_callback(last_result):
        f = EasyFuture()
        f.set_result(f"result: {last_result}")
        return f
    f2 = f1.then(then_callback)
    f1.set_result("f1 ok")
    assert (await f2) == 'result: f1 ok', "if inside future has result, then_future will has result too"

    # test callback fail
    f1 = EasyFuture()

    def then_callback(last_result):
        f = EasyFuture()
        f.set_exception(Exception(f"result: {last_result}"))
        return f

    f2 = f1.then(then_callback)
    f1.set_result("f1 ok")
    with pytest.raises(Exception, match='result: f1 ok'):
        await f2

    # test upstream fail
    # test inside future ok
    f1 = EasyFuture()
    result = None

    def else_callback(last_exception: Exception):
        f = EasyFuture()
        f.set_result(f"f1 exception {last_exception.args[0]}")
        return f

    f2 = f1.catch(else_callback)
    f1.set_exception(Exception("f1 bad"))
    assert (await f2) == 'f1 exception f1 bad'

    # test inside future exception
    f1 = EasyFuture()
    result = None

    def else_callback(last_exception: Exception):
        f = EasyFuture()
        f.set_exception(Exception(f"f1 exception {last_exception.args[0]}"))
        return f

    f2 = f1.then(None, else_callback)
    f1.set_exception(Exception("f1 bad"))
    with pytest.raises(Exception, match='f1 exception f1 bad'):
        await f2

    # upstream cancelled
    f1 = EasyFuture()

    def else_callback(last_exception: Exception):
        f = EasyFuture()
        f.set_exception(Exception(f"f1 exception {last_exception.args[0]}"))
        return f

    f2 = f1.then(None, else_callback)
    f1.cancel('f1 cancelled')
    with pytest.raises(asyncio.exceptions.CancelledError, match='Upstream future cancelled'):
        await f2

    # callback future cancelled
    f1 = EasyFuture()

    def then_callback(result):
        f = EasyFuture()
        f.cancel(f"callback cancelled with f1 {result}")
        return f

    f2 = f1.then(then_callback)
    f1.set_result('f1 ok')
    with pytest.raises(asyncio.exceptions.CancelledError, match='callback cancelled with f1 f1 ok'):
        await f2

    # test no right call back
    f1 = EasyFuture()

    def else_callback(result):
        f = EasyFuture()
        f.cancel(f"f1 ok {result}")
        return f

    f2 = f1.then(None, else_callback)
    f1.set_result('f1 ok')
    assert (await f2) == 'f1 ok', 'If no suitable callback, then clone the result'

def test_refcount():
    # test then method
    f1 = EasyFuture()
    assert sys.getrefcount(f1) == 2, "new created future has 2 refcount"
    def then_cb():
        return EasyFuture().resolve(True)
    def else_cb():
        return EasyFuture().resolve(True)
    f1.then(then_cb(), else_cb)
    assert sys.getrefcount(f1) == 2, "after add then else db, future has 2 refcount"

    #test cascade method
    core_future = asyncio.get_event_loop().create_future()
    assert sys.getrefcount(core_future) == 2, "new created future has 2 refcount"
    custom_future = EasyFuture()
    custom_future.cascade(core_future)
    assert sys.getrefcount(core_future) == 2, "after cascade, core_future future has 2 refcount"
    assert sys.getrefcount(custom_future) == 3, "after cascade, custom future has 3 refcount"

    # test wrap method
    core_future = asyncio.get_event_loop().create_future()
    custom_future = EasyFuture.wrap(core_future)
    assert sys.getrefcount(core_future) == 2, "after cascade, core_future future has 2 refcount"
    assert sys.getrefcount(custom_future) == 3, "after cascade, custom future has 3 refcount"
