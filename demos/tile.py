# Demos infinite, procedurally generated tiles

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow

import tkinter as tk
import tkinter.ttk as ttk
import PIL.Image, PIL.ImageDraw, PIL.ImageFont

root = tk.Tk()
tilewindow.util.centre_window_percentage(root, 50, 50)
tilewindow.util.stretch(root, [0], [0])

font = PIL.ImageFont.truetype("arial.ttf", size=20)

class OurProvider(tilewindow.TileProvider):
    def __call__(self, tx, ty):
        size = 128
        image = PIL.Image.new("L", (size, size), color=255)
        draw = PIL.ImageDraw.Draw(image)
        draw.line([(0, 0), (size-1, 0), (size-1, size-1), (0, size-1), (0, 0)])
        draw.text((30,50), "({},{})".format(tx,ty), font=font)
        return image

image = tilewindow.TileImage(root, OurProvider(), 128)
image.grid(row=0, column=0, sticky=tk.NSEW)

class PositionPrinter(tilewindow.image.MouseHandler):
    def __init__(self):
        self.label = ttk.Label()

    def notify(self, x, y):
        self.label["text"] = "Current position: ({},{})".format(x, y)

image.mouse_handler = PositionPrinter()
image.mouse_handler.label.grid(row=1, column=0, sticky=tk.W)
image["cursor"] = "crosshair"
image.mouse_handler = tilewindow.image.MouseCursorHandler(image, image.mouse_handler)

root.mainloop()