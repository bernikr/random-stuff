import asyncio
import cgi
import json
import os
import time
import zlib
from dataclasses import dataclass, field

import aiohttp as aiohttp
from dotenv import load_dotenv
import requests

load_dotenv()
HA_TOKEN = os.getenv('HA_TOKEN')
HA_URL = os.getenv('HA_URL')
MAP_ENTITY = 'camera.map_data'

@dataclass
class Chunk:
    type: str
    data: bytes = field(repr=False)


def parse_png_chunks(img: bytes) -> [Chunk]:
    assert img[0:8] == b'\x89PNG\r\n\x1a\n', 'Invalid PNG header'

    i = 8
    while i < len(img):
        chunk_length = int.from_bytes(img[i:i + 4], 'big')
        chunk_type = img[i + 4:i + 8]
        yield Chunk(type=chunk_type.decode(), data=img[i + 8:i + 8 + chunk_length])
        i += 12 + chunk_length


async def get_x_mixed_replace(s, url):
    async with s.get(url) as r:
        mime, content_options = cgi.parse_header(r.headers['Content-Type'])
        assert mime == 'multipart/x-mixed-replace'

        length = 0
        while True:
            line = (await r.content.readuntil(b'\n')).rstrip()
            if line.startswith(b'Content-Length: '):
                length = int(line[16:])
            elif line == b'' and length:
                yield await r.content.readexactly(length)
                length = 0


async def main():
    async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {HA_TOKEN}'}) as s:
        async with s.get(f'{HA_URL}/api/states/{MAP_ENTITY}') as r:
            img_token = (await r.json())['attributes']['access_token']

        lasttime = time.time()
        async for img in get_x_mixed_replace(s, f'{HA_URL}/api/camera_proxy_stream/{MAP_ENTITY}?token={img_token}'):
            map_data = next(c.data[13:] for c in parse_png_chunks(img)
                            if c.type == 'zTXt' and c.data.startswith(b'ValetudoMap\0'))
            map_data = zlib.decompress(map_data)
            map_data = json.loads(map_data)

            print("--map_data")
            print(f"{time.time()-lasttime:.2f}s")
            lasttime = time.time()
        print("end")


if __name__ == '__main__':
    asyncio.run(main())
