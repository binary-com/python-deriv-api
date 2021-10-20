import websockets
import asyncio
from rx.subject import Subject
import json
connection = None;
connection_closed = False
response_subject = Subject()
response_subject.subscribe(lambda data: print(f"data is {data['req_id']}"))
async def wait_message():
    while not connection_closed:
        response = await connection.recv()
        response_subject.on_next(json.loads(response))

async def subscribe_stream(request):
    await connection.send(json.dumps(request))

async def main():
    global connection
    connection = await websockets.connect('wss://frontend.binaryws.com/websockets/v3?app_id=1089&l=EN&brand=')
    asyncio.create_task(wait_message())
    await asyncio.create_task(subscribe_stream({
  "ticks": "R_50",
  "subscribe": 1,
  "req_id": 1
}))
    await asyncio.create_task(subscribe_stream({
        "ticks": "R_100",
        "subscribe": 1,
        "req_id": 2
    }))

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.run_forever()