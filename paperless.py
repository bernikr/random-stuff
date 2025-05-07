import asyncio
import datetime
import os
import re

from pypaperless import Paperless

PAPERLESS_URL = os.environ["PAPERLESS_URL"]
PAPERLESS_TOKEN = os.environ["PAPERLESS_TOKEN"]


async def main() -> None:
    async with Paperless(PAPERLESS_URL, PAPERLESS_TOKEN) as pl:
        async for doc in pl.documents:
            if doc.title is None:
                continue
            if res := re.match(r"(\d{4}) (\d{2}) (\d{2}) (.*)", doc.title):
                y, m, d, title = res.groups()
                doc.title = title
                doc.created_date = datetime.date(int(y), int(m), int(d))
                print(f"updated {doc.title}")
                await doc.update()
            elif res := re.match(r"(\d{4}) (\d{2}) (.*)", doc.title):
                y, m, title = res.groups()
                doc.title = title
                doc.created_date = datetime.date(int(y), int(m), 1)
                print(f"updated {doc.title}")
                await doc.update()
            elif res := re.match(r"(\d{4}) (.*)", doc.title):
                y, title = res.groups()
                doc.title = title
                doc.created_date = datetime.date(int(y), 1, 1)
                print(f"updated {doc.title}")
                await doc.update()


asyncio.run(main())
