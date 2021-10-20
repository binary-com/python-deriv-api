# run it like PYTHONPATH=. python3 examples/simple_bot1.py
import sys
import asyncio
import os
from deriv_api import deriv_api
from rx import Observable
app_id = 1089


async def sample_calls():
    api = deriv_api.DerivAPI(app_id=app_id)
    wait_tick = api.expect_response('tick')
    last_data = {}
    source_tick_50: Observable  = await api.subscribe({'ticks': 'R_50'})
    def create_subs_cb(symbol):
        count = 1
        def cb(data):
            nonlocal count
            count = count + 1
            last_data[symbol] = data
            print(f"get symbol {symbol} {count}")
        return cb

    source_tick_50.subscribe(create_subs_cb('R_50'))
    source_tick_100: Observable  = await api.subscribe({'ticks': 'R_100'})
    source_tick_100.subscribe(create_subs_cb('R_100'))
    first_tick = await wait_tick
    print(f"first tick is {first_tick}")
    await asyncio.sleep(5)
    print("now will forget")
    #await api.forget(last_data['R_50']['subscription']['id'])
    #await api.forget(last_data['R_100']['subscription']['id'])
    await api.forget_all('ticks')
    await asyncio.sleep(5)
    await api.clear()

asyncio.run(sample_calls())
