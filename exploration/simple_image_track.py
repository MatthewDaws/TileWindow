# Shows how to directly use the `DragTrack` class to view a large image, in a
# resizable window.

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow.util.util as util
from tilewindow.util.drag_track import DragTrack

import tkinter as tk
import tkinter.ttk as ttk
import PIL.Image, PIL.ImageTk

root = tk.Tk()
util.centre_window_percentage(root, 50, 50)
util.stretch(root, [0], [0])

label_frame = ttk.LabelFrame(root, text="Label Frame", width=200, height=200)
label_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=10, pady=10)
util.stretch(label_frame, [0], [0])

canvas = tk.Canvas(label_frame, borderwidth=0, highlightthickness=0)
canvas.grid(sticky=tk.NSEW, padx=10, pady=10)

class OurTrack(DragTrack):
    def __init__(self, canvas):
        super().__init__(canvas)
        self.canvas = canvas
        self.photo = PIL.ImageTk.PhotoImage(self.make_image())
        self.image_id = canvas.create_image(0, 0, anchor=tk.NW)
        self.canvas.itemconfigure(self.image_id, image=self.photo)
        self.canvas.bind("<Configure>", self._conf)
        self._start = None

    def _conf(self, event):
        self.canvas.winfo_width(), self.canvas.winfo_height()


    def make_image(self):
        image = PIL.Image.new("RGB", (1000, 800))
        import array
        data = array.array("B")
        for y in range(800):
            for x in range(1000):
                data.append(x % 256)
                data.append(y % 256)
                data.append((x+y) % 256)
        image.frombytes(bytes(data))
        return image

    def moved(self, dx, dy, new):
        # Also possible to move the image itself.
        #if new:
        #    self._start = tuple(int(x) for x in self.canvas.coords(self.image_id))
        #    print(self._start)
        #x, y = self._start[0] + dx, self._start[1] + dy
        #self.canvas.coords(self.image_id, x, y)
        if new:
            self._start = self.canvas.canvasx(0), self.canvas.canvasy(0)
        x, y = dx - self._start[0], dy - self._start[1]
        canvas.scan_dragto(int(x), int(y), gain=1)

OurTrack(canvas)

root.mainloop()