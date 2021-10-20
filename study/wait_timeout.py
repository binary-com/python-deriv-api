import asyncio
async def main():
    f1 = asyncio.get_event_loop().create_future()
    print(id(f1))
    done, pending = await asyncio.wait({f1}, timeout=1)
    print(pending)

asyncio.run(main())