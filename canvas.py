import asyncio
import tkinter as tk
import numpy as np


def apply_transform(t, x, y):
    res = np.matmul(t, [x, y, 1])
    return res[0], res[1]


def add_scale_transform(t, s):
    xo, yo, xs, ys = s
    t = np.matmul([[1, 0, -xo], [0, 1, -yo], [0, 0, 1]], t)
    t = np.matmul([[xs, 0, 0], [0, ys, 0], [0, 0, 1]], t)
    t = np.matmul([[1, 0, xo], [0, 1, yo], [0, 0, 1]], t)
    return t


class ResizingCanvas(tk.Canvas):
    transform = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    def __init__(self, parent, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)
        self.bind("<Configure>", self.on_resize)
        self.height = self.winfo_reqheight()
        self.width = self.winfo_reqwidth()

    def on_resize(self, event):
        self.config(width=self.width, height=self.height)

    def _create(self, itemType, args, kw):
        output = []
        for x, y in zip(args[0::2], args[1::2]):
            output.extend(apply_transform(self.transform, x, y))
        super()._create(itemType, tuple(output), kw)

    def scale(self, tag, xo, yo, xs, ys):
        if tag == "all":
            self.transform = add_scale_transform(self.transform, (xo, yo, xs, ys))
        super().scale(tag, xo, yo, xs, ys)


class ScrolFrame(tk.Frame):
    def __init__(self, root):
        tk.Frame.__init__(self, root)
        self.canvas = ResizingCanvas(self, width=400, height=400)
        self.pack(fill=tk.BOTH, expand=tk.YES)
        self.canvas.pack(fill=tk.BOTH, expand=tk.YES)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self.scroll_start)
        self.canvas.bind("<B1-Motion>", self.scroll_move)
        self.canvas.bind("<Button-4>", self.zoomerP)
        self.canvas.bind("<Button-5>", self.zoomerM)
        self.canvas.bind("<MouseWheel>", self.zoomer)
        root.bind_all("<MouseWheel>", self.zoomer)

    def scroll_start(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def scroll_move(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoomer(self, event):
        if event.delta > 0:
            self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), 1.1, 1.1)
        elif event.delta < 0:
            self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), 0.9, 0.9)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomerP(self, event):
        self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), 1.1, 1.1)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoomerM(self, event):
        self.canvas.scale("all", self.canvas.canvasx(event.x), self.canvas.canvasy(event.y), 0.9, 0.9)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


class CanvasWindow:
    def __init__(self):
        self._root = tk.Tk()
        self._frame = ScrolFrame(self._root)

    @property
    def canvas(self) -> tk.Canvas:
        return self._frame.canvas

    def mainloop(self):
        self._root.mainloop()

    async def async_mainloop(self):
        while True:
            try:
                self._root.update()
            except tk.TclError:
                return
            await asyncio.sleep(0)


async def test(c):
    while True:
        c.create_line(0, 0, 200, 100)
        await asyncio.sleep(1)


async def main():
    cw = CanvasWindow()

    c = cw.canvas
    c.create_line(0, 0, 200, 100)
    c.create_line(0, 100, 200, 0, fill="red", dash=(4, 4))
    c.create_rectangle(50, 25, 150, 75, fill="blue")

    asyncio.create_task(test(c))
    await cw.async_mainloop()


if __name__ == "__main__":
    asyncio.run(main())
