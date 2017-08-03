# Display a image and allow zooming in and out and scrolling

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog
import PIL.Image

root = tk.Tk()
tilewindow.util.stretch(root, rows=[1], columns=[0])

frame = ttk.Frame(root)
tilewindow.util.stretch(frame, [0], [0])
frame.grid(sticky=tk.NSEW, row=1)

image_widget = tilewindow.Image(frame)
image_widget.grid(row=0, column=0, sticky=tk.NSEW)
xscroll, yscroll = image_widget.make_scroll_bars(frame)
yscroll.grid(row=0, column=1, sticky=tk.NS)
xscroll.grid(row=1, column=0, sticky=tk.EW)

filename = tkinter.filedialog.askopenfilename(parent=root, filetypes=[("PNG file", "*.png"),
    ("JPEG file", "*.jpg"), ("Other PIL supported file", "*.*")])
image = PIL.Image.open(filename)
image_widget.set_image(image, allow_zoom=True)

xscroll.set_to_hide()
yscroll.set_to_hide()


frame = ttk.Frame(root)
frame.grid(sticky=tk.NSEW, row=0)
def no_zoom():
    image_widget.zoom = 1.0
ttk.Button(frame, text="Restore zoom", command=no_zoom).grid(row=0, column=0)
def zoom():
    w, h = image_widget.size
    zw = w / image.width
    zh = h / image.height
    image_widget.zoom = min(zw, zh)
ttk.Button(frame, text="Zoom to window", command=zoom).grid(row=0, column=1)

root.mainloop()
