from rx.subject import Subject
from rx.operators import first, to_future
import asyncio

async def main():
    sub1 = Subject()
    async def send_error():
        await asyncio.sleep(1)
        sub1.on_error(Exception('hello'))
    asyncio.create_task(send_error())
    f1 = sub1.pipe(first(), to_future())
    try:
        await f1
    except Exception as err:
        print(f"{err}")
    print(f"is done? {f1.done()}")

asyncio.run(main())

