import cgi
import json
import os
import time
import zlib
from dataclasses import dataclass, field

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


def parse_x_mixed_replace(r):
    mime, content_options = cgi.parse_header(r.headers['Content-Type'])
    assert mime == 'multipart/x-mixed-replace'

    buffer, header, length = b'', True, 0
    for c in r.iter_content():
        buffer += c
        if header:
            if (i := buffer.find(b'\n')) >= 0:
                line = buffer[:i].rstrip()
                if line.startswith(b'Content-Length: '):
                    length = int(line[16:])
                elif line == b'' and length:
                    header = False
                buffer = buffer[i+1:]
        else:
            length -= len(c)
            if length == 0:
                yield buffer
                buffer = b''
                header = True
            elif length < 0:
                yield buffer[:length]
                buffer = buffer[length:]
                header = True
                length = 0


def main():
    r = requests.get(f'{HA_URL}/api/states/{MAP_ENTITY}', headers={'Authorization': f'Bearer {HA_TOKEN}'})
    img_token = r.json()['attributes']['access_token']
    with requests.get(f'{HA_URL}/api/camera_proxy_stream/{MAP_ENTITY}?token={img_token}', stream=True) as r:
        lasttime = time.time()
        for img in parse_x_mixed_replace(r):
            map_data = next(c.data[13:] for c in parse_png_chunks(img)
                            if c.type == 'zTXt' and c.data.startswith(b'ValetudoMap\0'))
            map_data = zlib.decompress(map_data)
            map_data = json.loads(map_data)

            print("--map_data")
            print(f"{time.time()-lasttime:.2f}s")
            lasttime = time.time()
    print("end")


if __name__ == '__main__':
    main()
