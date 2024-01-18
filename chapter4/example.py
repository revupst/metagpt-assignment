import asyncio

from .callback import discord_callback
from .watcher import OssWatcher


async def main():
    msg = "https://github.com/trending"
    role = OssWatcher()
    result = await role.run(msg)
    await discord_callback(result)


if __name__ == "__main__":
    asyncio.run(main())
