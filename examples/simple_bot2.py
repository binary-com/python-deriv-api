import sys
sys.path.append('.')
import asyncio
import os
from deriv_api import DerivAPI
import websockets


app_id = 1089
api_token = os.getenv('DERIV_TOKEN', '')

if len(api_token) == 0:
    sys.exit("DERIV_TOKEN environment variable is not set")

async def connect():
    url = f'wss://frontend.binaryws.com/websockets/v3?l=EN&app_id={app_id}'
    connection = await websockets.connect(url)

    return connection

async def sample_calls():
    # create your own websocket connection and pass it as argument to DerivAPI
    connection = await connect()
    api = DerivAPI(connection=connection)

    response = await api.ping({'ping':1})
    if response['ping']:
        print(response['ping'])

    """ 
    To test deriv_api try reconnect automatically on disconnecting, uncomment the below comment then run this script
    disconnect your network & reconnect back. Enable the loglevel to logging.DEBUG to see the ping/pong 
    """
    # await asyncio.sleep(300)

    # Authorize
    authorize = await api.authorize(api_token)
    print(authorize)

    # Get Balance
    response = await api.balance()
    response = response['balance']
    currency = response['currency']
    print("Your current balance is", response['currency'], response['balance'])

    # Get active symbols from cache
    cached_active_symbols = await api.cache.active_symbols({"active_symbols": "brief", "product_type": "basic"})
    print(cached_active_symbols)

    # Get assets
    assets = await api.cache.asset_index({"asset_index": 1})
    print(assets)
    await api.clear()

asyncio.run(sample_calls())
