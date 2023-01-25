from utils import *
import asyncio

async def main():
    sd, so = await run_comman_d("dir /B")
    for line in so.split("\n"):
        print(line.rsplit("\t", 1)[-1].split(" ", 1)[-1])

asyncio.run(main())