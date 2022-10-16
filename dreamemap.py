import asyncio
import zlib
from collections import defaultdict
from dataclasses import dataclass, field

from canvas import CanvasWindow, Canvas


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


def unfilter_line(line):
    assert line[0] == 1
    output = b''
    prev = 0
    for c in line[1:]:
        prev = (prev + c) % 256
        output += prev.to_bytes(1, 'big')
    return output


def load_map_file(path):
    with open(path, "rb") as img:
        chunks = list(parse_png_chunks(img.read()))
    header = chunks[0]
    assert header.type == 'IHDR'
    width = int.from_bytes(header.data[0:4], 'big')
    height = int.from_bytes(header.data[4:8], 'big')
    assert header.data[8:13] == b'\x08\0\0\0\0'
    assert chunks[1].type == 'IDAT'
    data = zlib.decompress(chunks[1].data)
    lines = [unfilter_line(data[i:i+width+1]) for i in range(0, (width+1)*height, (width+1))]
    return lines


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


async def load_map(c: Canvas):
    map = load_map_file("test/segmented_map.png")
    segments = defaultdict(list)
    for y, line in enumerate(map):
        for x, a in enumerate(line):
            if a:
                segments[a].append((x, y))

    for a in segments:
        for x1, y1, x2, y2 in pixels_to_rects(segments[a]):
            c.add_to_layer(1, c.create_rectangle, (x1, y1, x2, y2), fill='#E85959', width=0)


async def main():
    cw = CanvasWindow()
    asyncio.create_task(load_map(cw.canvas))
    await cw.async_mainloop()


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
