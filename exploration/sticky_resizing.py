# Shows how a canvas gets dynamically resized using `tkinter`.
# Basically, pretty boring.  But notice that there is no clipping of the
# text widget to be inside the notion width/height of the canvas

import os, sys
sys.path.insert(0, os.path.abspath(os.path.join("..")))

import tilewindow.util.util as util

import tkinter as tk
import tkinter.ttk as ttk

root = tk.Tk()
util.centre_window_percentage(root, 50, 50)
util.stretch(root, [0], [0])

label_frame = ttk.LabelFrame(root, text="Label Frame")
label_frame.grid(sticky=tk.NSEW, padx=10, pady=10)
util.stretch(label_frame, [0], [0])

canvas = tk.Canvas(label_frame, borderwidth=0, highlightthickness=0, width=200, height=200)
canvas.grid(sticky=tk.NSEW, padx=10, pady=10)
text_id = canvas.create_text(20, 20, anchor=tk.NW)

def conf(event):
    text = "Try resizing the main window!\n"
    text += "We have used 10 pixels of padding.\n"
    text += "<Configure> event = {}\n".format(event)
    text += "canvas widget size: {}x{}\n".format(canvas["width"], canvas["height"])
    text += "canvas winfo_geometry: {}\n".format(canvas.winfo_geometry())
    text += "canvas winfo width/height: {}x{}\n".format(canvas.winfo_width(), canvas.winfo_height())
    text += "canvas winfo req width/height: {}x{}".format(canvas.winfo_reqwidth(), canvas.winfo_reqheight())
    canvas.itemconfigure(text_id, text = text)

canvas.bind("<Configure>", conf)

stretch_weight = 1
def toggle_stretch(event=None):
    global stretch_weight
    stretch_weight = 1 - stretch_weight
    label_frame.rowconfigure(0, weight=stretch_weight)

ttk.Button(root, text="Click to change frame stretchy", command=toggle_stretch).grid(row=1, column=0, padx=5, pady=5)

root_stretch_weight = 1
def root_toggle_stretch(event=None):
    global root_stretch_weight
    root_stretch_weight = 1 - root_stretch_weight
    root.rowconfigure(0, weight=root_stretch_weight)

ttk.Button(root, text="Click to change window stretchy", command=root_toggle_stretch).grid(row=2, column=0, padx=5, pady=5)

root.mainloop()
