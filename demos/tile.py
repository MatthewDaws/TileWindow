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

class PositionPrinter(tilewindow.image.MouseHandlerChain):
    def __init__(self, parent, delegate):
        super().__init__(delegate)
        self.label = ttk.Label(parent)

    def notify(self, x, y):
        self.label["text"] = "Current position: ({},{})".format(x, y)
        super().notify(x, y)

image["cursor"] = "crosshair"

frame = ttk.Frame(root)
frame.grid(row=1, column=0, sticky=tk.W)
image.mouse_handler = PositionPrinter(frame, tilewindow.image.MouseCursorHandler(image, image.mouse_handler))
#image.mouse_handler = PositionPrinter(frame)
image.mouse_handler.label.grid(row=0, column=0, sticky=tk.W)
ttk.Button(frame, text="Move to (0,0)", command = lambda : 
    image.move_tile_view_to(0, 0)).grid(row=0, column=1)
ttk.Button(frame, text="Move to (10,0)", command = lambda : 
    image.move_tile_view_to(1280, 0)).grid(row=0, column=2)
ttk.Button(frame, text="Move to (0,10)", command = lambda : 
    image.move_tile_view_to(0, 1280)).grid(row=0, column=3)
ttk.Button(frame, text="Move to (10,10)", command = lambda : 
    image.move_tile_view_to(1280, 1280)).grid(row=0, column=4)
ttk.Button(frame, text="Move to (2.5,2.5)", command = lambda : 
    image.move_tile_view_to(320, 320)).grid(row=0, column=5)

root.mainloop()