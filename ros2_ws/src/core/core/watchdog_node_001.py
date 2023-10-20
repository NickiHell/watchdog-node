import asyncio


async def main():
    await asyncio.sleep(60 * 5)


if __name__ == '__main__':
    asyncio.run(main())
