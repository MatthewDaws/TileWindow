# View a (large) image

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow

import tkinter as tk
import tkinter.ttk as ttk
import PIL.Image

def make_image(size="large"):
    if size == "large":
        image = PIL.Image.new("RGB", (800, 600))
    else:
        image = PIL.Image.new("RGB", (600, 400))
    import array
    data = array.array("B")
    for y in range(image.height):
        for x in range(image.width):
            data.append(x % 256)
            data.append(y % 256)
            data.append((x+y) % 256)
    image.frombytes(bytes(data))
    return image

root = tk.Tk()
tilewindow.util.stretch(root, [0], [0])
image_widget = tilewindow.Image(root)
image_widget.grid(row=0, column=0, sticky=tk.NSEW)
image_widget.set_image(make_image(), True)

labels = [
    [tk.NW, tk.N, tk.NE],
    [tk.W, tk.CENTER, tk.E],
    [tk.SW, tk.S, tk.SE]
]
meta_frame = ttk.Frame(root)
meta_frame.grid(row=1, column=0)
frame = ttk.LabelFrame(meta_frame, text="Anchor point")
frame.grid(row=0, column=0)
for j, row in enumerate(labels):
    for i, la in enumerate(row):
        def cmd(x=la):
            image_widget.anchor = x
        b = ttk.Button(frame, text=la, command = cmd)
        b.grid(row=j, column=i)

frame = ttk.Frame(meta_frame)
frame.grid(row=0, column=1)
def set_image(size):
    image_widget.set_image(make_image(size), True)
ttk.Button(frame, text="Large image", command = lambda : set_image("large")).grid(row=0, column=0)
ttk.Button(frame, text="Small image", command = lambda : set_image("small")).grid(row=1, column=0)

frame = ttk.Frame(meta_frame)
frame.grid(row=0, column=2)
def set_free(b):
    image_widget.free = b
ttk.Button(frame, text="Clamp to image", command = lambda : set_free(False)).grid(row=0, column=0)
ttk.Button(frame, text="Free scrolling", command = lambda : set_free(True)).grid(row=1, column=0)

frame = ttk.Frame(meta_frame)
frame.grid(row=0, column=3)
def set_zoom(b):
    image_widget.zoom = b
ttk.Button(frame, text="Normal zoom", command = lambda : set_zoom(1)).grid(row=0, column=0)
ttk.Button(frame, text="Zoom in x2", command = lambda : set_zoom(2)).grid(row=1, column=0)
ttk.Button(frame, text="Zoom out x2", command = lambda : set_zoom(0.5)).grid(row=2, column=0)

image_widget.mouse_handler = tilewindow.image.MouseCursorHandler(image_widget)
image_widget["cursor"] = "crosshair"

root.mainloop()
