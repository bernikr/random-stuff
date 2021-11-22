import asyncio
import cgi
import json
import logging
import os
import zlib
from collections import defaultdict
from dataclasses import dataclass, field

import aiohttp as aiohttp
from dotenv import load_dotenv

from canvas import CanvasWindow, Canvas

logging.basicConfig(
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.DEBUG
)

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
        while not r.content.at_eof():
            line = (await r.content.readuntil(b'\n')).rstrip()
            if line.startswith(b'Content-Length: '):
                length = int(line[16:])
            elif line == b'' and length:
                yield await r.content.readexactly(length)
                length = 0


def pixels_to_rects(pixels):
    pixel_set = set(pixels)

    for tl in sorted(pixel_set):
        if tl not in pixel_set:
            continue
        pixel_set.remove(tl)

        br = [tl[0] + 1, tl[1] + 1]

        changed = True
        while changed:
            changed = False
            if all((i, br[1]) in pixel_set for i in range(tl[0], br[0])):
                pixel_set.difference_update((i, br[1]) for i in range(tl[0], br[0]))
                br[1] += 1
                changed = True
            if all((br[0], i) in pixel_set for i in range(tl[1], br[1])):
                pixel_set.difference_update((br[0], i) for i in range(tl[1], br[1]))
                br[0] += 1
                changed = True
        yield *tl, *br


COLOR_LIST = [
    '#E85959',
    '#E8C659',
    '#504DA2',
    '#47BA47',
]


def get_layer_drawing_options(layer):
    lt = layer['type']
    if lt == 'wall':
        return {'fill': 'black', 'width': 0}
    elif lt == 'floor':
        return {'fill': 'gray', 'width': 0, 'stipple': 'gray12'}
    elif lt == 'segment':
        return {'fill': COLOR_LIST[layer['metaData']['segmentId']-1], 'width': 0}
    else:
        assert False, f'Unknown layer type `{lt}`'


LAYERS = defaultdict(lambda: 0)
LAYERS.update({
    'wall': 3,
    'floor': 2,
    'segment': 1,
})


def draw_layer(c: Canvas, layer, s):
    pixels = layer['pixels']
    pixels = zip(pixels[0::2], pixels[1::2])
    for x1, y1, x2, y2 in pixels_to_rects(pixels):
        c.add_to_layer(LAYERS[layer['type']],
                       c.create_rectangle, (x1*s, y1*s, x2*s, y2*s), **get_layer_drawing_options(layer))


def draw_entities(c: Canvas, e):
    cl = e['__class']
    if cl == 'PointMapEntity':
        s = 10
        x, y = e['points']
        c.create_oval(x-s, y-s, x+s, y+s, fill='black')
    elif cl == 'PolygonMapEntity':
        c.create_polygon(*e['points'], fill='', width=2, outline='red')
    elif cl == 'PathMapEntity':
        if len(e['points']) >= 4:
            c.create_line(*e['points'], width=2, fill='black')
    else:
        assert False, f'Unknown entity class `{cl}`'

async def load_map(c: Canvas):
    async with aiohttp.ClientSession(headers={'Authorization': f'Bearer {HA_TOKEN}'}) as s:
        async with s.get(f'{HA_URL}/api/states/{MAP_ENTITY}') as r:
            img_token = (await r.json())['attributes']['access_token']

        async for img in get_x_mixed_replace(s, f'{HA_URL}/api/camera_proxy_stream/{MAP_ENTITY}?token={img_token}'):
            map_data = next(c.data[13:] for c in parse_png_chunks(img)
                            if c.type == 'zTXt' and c.data.startswith(b'ValetudoMap\0'))
            map_data = zlib.decompress(map_data)
            map_data = json.loads(map_data)
            logging.info('new map data')
            c.delete('all')
            for l in map_data['layers']:
                draw_layer(c, l, map_data['pixelSize'])
            for e in map_data['entities']:
                draw_entities(c, e)


async def main():
    cw = CanvasWindow()
    t = asyncio.create_task(load_map(cw.canvas))
    await cw.async_mainloop()


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
